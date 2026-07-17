"""Compile canonical agent plans into provider-runtime input batches.

This module intentionally does not import a provider runtime, start a process,
or invoke a LangGraph server.  The provider runtime remains the sole execution
owner; this boundary only determines dependency-safe request ordering.
"""
from __future__ import annotations

from collections.abc import Iterable

from servicefabric_agent_provider_contracts import ProviderExecutionRequest, ProviderPolicy
from servicefabric_agentic_contracts import AgentRunPlan, AgentTask


class LangGraphOrchestrator:
    """Create deterministic dependency layers using shared provider contracts."""

    def compile(
        self,
        plan: AgentRunPlan,
        policy: ProviderPolicy,
        *,
        repository: str,
        timeout_seconds: int | None = None,
        model: str | None = None,
        environment_names: tuple[str, ...] = (),
    ) -> tuple[tuple[ProviderExecutionRequest, ...], ...]:
        """Return ready-to-execute batches without performing execution.

        Each batch contains independent tasks.  Batches are deterministically
        split to respect the plan's total concurrency and policy's per-provider
        concurrency limit.  The provider runtime owns actual scheduling and
        all subprocess lifecycle behaviour.
        """
        if not repository:
            raise ValueError("repository must not be empty")

        tasks = {task.task_id: task for task in plan.tasks}
        if len(tasks) != len(plan.tasks):
            raise ValueError("task identifiers must be unique")
        missing = sorted(
            dependency
            for task in plan.tasks
            for dependency in task.dependencies
            if dependency not in tasks
        )
        if missing:
            raise ValueError(f"plan has unknown task dependencies: {', '.join(missing)}")

        remaining = {task.task_id: set(task.dependencies) for task in plan.tasks}
        batches: list[tuple[ProviderExecutionRequest, ...]] = []
        completed: set[str] = set()
        while remaining:
            ready = tuple(task for task in plan.tasks if task.task_id in remaining and remaining[task.task_id] <= completed)
            if not ready:
                raise ValueError("plan contains a dependency cycle")

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
                for task in ready
            )
            batches.extend(self._split_batch(requests, plan.maximum_parallel_tasks, policy.maximum_parallel_per_provider))
            completed.update(task.task_id for task in ready)
            for task in ready:
                del remaining[task.task_id]

        return tuple(batches)

    @staticmethod
    def _request_for(
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
        return ProviderExecutionRequest(
            run_id=run_id,
            task_id=task.task_id,
            provider_id=policy.provider_for_role(task.role),
            repository=repository,
            prompt=LangGraphOrchestrator._render_prompt(task),
            timeout_seconds=timeout_seconds,
            maximum_turns=maximum_turns,
            model=model,
            environment_names=environment_names,
            metadata={"role": task.role},
        )

    @staticmethod
    def _render_prompt(task: AgentTask) -> str:
        sections = [f"Objective:\n{task.objective}"]
        for heading, values in (
            ("Allowed paths", task.allowed_paths),
            ("Forbidden paths", task.forbidden_paths),
            ("Required context", task.required_context),
            ("Expected outputs", task.expected_outputs),
            ("Verification", task.verification_commands),
        ):
            if values:
                sections.append(f"{heading}:\n" + "\n".join(f"- {value}" for value in values))
        return "\n\n".join(sections)

    @staticmethod
    def _split_batch(
        requests: Iterable[ProviderExecutionRequest],
        maximum_total: int,
        maximum_per_provider: int,
    ) -> tuple[tuple[ProviderExecutionRequest, ...], ...]:
        batches: list[list[ProviderExecutionRequest]] = []
        for request in requests:
            for batch in batches:
                provider_count = sum(item.provider_id == request.provider_id for item in batch)
                if len(batch) < maximum_total and provider_count < maximum_per_provider:
                    batch.append(request)
                    break
            else:
                batches.append([request])
        return tuple(tuple(batch) for batch in batches)
