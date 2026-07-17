"""Prepare provider-runtime inputs from authoritative Wave-7 task state."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from servicefabric_agent_harness import CodexPromptHarness
from servicefabric_agent_provider_contracts import ProviderExecutionRequest, ProviderPolicy
from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, AgentTaskResult
from servicefabric_agentic_orchestrator import ready_tasks
from servicefabric_agentic_run_store import FileRunStore


@dataclass(frozen=True)
class LangGraphExecutionCursor:
    """Orchestration-only checkpoint; durable task state remains in FileRunStore."""

    run_id: str
    dispatched_task_ids: tuple[str, ...] = ()
    interrupt: str | None = None


class LangGraphOrchestrator:
    """Translate ready Wave-7 tasks to provider requests without execution."""

    def __init__(self, harness: CodexPromptHarness | None = None) -> None:
        self._harness = harness or CodexPromptHarness()

    @staticmethod
    def cursor(run_id: str, *, dispatched_task_ids: tuple[str, ...] = (), interrupt: str | None = None) -> LangGraphExecutionCursor:
        """Create a serializable orchestration cursor without copying task state."""
        return LangGraphExecutionCursor(run_id=run_id, dispatched_task_ids=dispatched_task_ids, interrupt=interrupt)

    def compile(
        self,
        plan: AgentRunPlan,
        policy: ProviderPolicy,
        store: FileRunStore,
        *,
        repository: str,
        timeout_seconds: int | None = None,
        model: str | None = None,
        environment_names: tuple[str, ...] = (),
    ) -> tuple[tuple[ProviderExecutionRequest, ...], ...]:
        """Return batches for ready tasks without reading or changing runtime state."""
        if not repository:
            raise ValueError("repository must not be empty")

        results = self._load_results(store, plan.run_id)
        requests = tuple(
            self._request_for(
                plan.run_id,
                task,
                policy,
                repository=repository,
                timeout_seconds=policy.timeout_seconds if timeout_seconds is None else timeout_seconds,
                maximum_turns=policy.maximum_turns,
                model=model,
                environment_names=environment_names,
            )
            for task in ready_tasks(plan, results)
        )
        return self._split_batch(requests, policy.maximum_parallel_per_provider)

    @staticmethod
    def _load_results(store: FileRunStore, run_id: str) -> tuple[AgentTaskResult, ...]:
        """Read only the run store's authoritative, validated task results."""
        state = store.load(run_id)
        return tuple(
            AgentTaskResult.model_validate(result)
            for result in state["results"].values()
        )

    def _request_for(
        self,
        run_id: str,
        task: AgentTask,
        policy: ProviderPolicy,
        *,
        repository: str,
        timeout_seconds: int,
        maximum_turns: int | None,
        model: str | None,
        environment_names: tuple[str, ...],
    ) -> ProviderExecutionRequest:
        task_pack = self._harness.prepare_task(task, repository)
        return ProviderExecutionRequest(
            run_id=run_id,
            task_id=task_pack["task_id"],
            provider_id=policy.provider_for_role(task.role),
            repository=task_pack["repository"],
            prompt=task_pack["prompt"],
            timeout_seconds=timeout_seconds,
            maximum_turns=maximum_turns,
            model=model,
            environment_names=environment_names,
            metadata={},
        )

    @staticmethod
    def _split_batch(
        requests: Iterable[ProviderExecutionRequest],
        maximum_per_provider: int,
    ) -> tuple[tuple[ProviderExecutionRequest, ...], ...]:
        batches: list[list[ProviderExecutionRequest]] = []
        for request in requests:
            for batch in batches:
                provider_count = sum(item.provider_id == request.provider_id for item in batch)
                if provider_count < maximum_per_provider:
                    batch.append(request)
                    break
            else:
                batches.append([request])
        return tuple(tuple(batch) for batch in batches)
