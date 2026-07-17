"""Integration-owned, resumable composition of the reviewed Wave-8 APIs."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from typing import Any

from servicefabric_agent_provider_contracts import ProviderEvent, ProviderExecutionResult, ProviderPolicy
from servicefabric_agent_provider_runtime import ProviderRuntime
from servicefabric_agentic_contracts import AgentTaskResult
from servicefabric_langgraph_orchestration import LangGraphOrchestrator

from .agent_providers import ProviderRegistry, load_provider_policy


_SECRET_KEYS = frozenset({"authorization", "credential", "key", "password", "secret", "token"})


class ProviderExecutionService:
    """Compose public APIs while FileRunStore remains task-state authority."""

    def __init__(self, agent_service: Any, registry: ProviderRegistry) -> None:
        self._agents = agent_service
        self._registry = registry
        self._runtime = ProviderRuntime(registry.adapters())
        self._orchestrator = LangGraphOrchestrator()

    def execute(self, run_id: str, policy_path: str | Path) -> dict[str, object]:
        policy = load_provider_policy(policy_path)
        cursor = self._load_cursor(run_id)
        cursor["policy"] = policy.model_dump(mode="json")
        self._save_cursor(run_id, cursor)
        return self._execute_with_policy(run_id, policy)

    def _execute_with_policy(self, run_id: str, policy: ProviderPolicy) -> dict[str, object]:
        plan, _ = self._agents._load(run_id)
        runtime_state = self._agents._load_runtime(run_id)
        repository = runtime_state["repository"]
        cursor = self._load_cursor(run_id)
        if cursor.get("interrupt"):
            return {"run_id": run_id, "interrupt": cursor["interrupt"], "handoff": self._agents.handoff(run_id).model_dump(mode="json")}

        batches = self._orchestrator.compile(plan, policy, self._agents.store, repository=repository)
        spent = self._spent(run_id)
        for batch in batches:
            if policy.maximum_total_cost is not None and spent >= policy.maximum_total_cost:
                return self._interrupt(run_id, "budget_excess")
            results = self._dispatch(batch, run_id)
            for task_id, result in results:
                spent += result.usage.estimated_cost
                task_result = result.task_result or AgentTaskResult(
                    task_id=task_id,
                    status="success" if result.status == "success" else "blocked" if result.status == "blocked" else "cancelled" if result.status == "cancelled" else "failed",
                    blockers=(f"provider result: {result.status}",) if result.status not in {"success", "cancelled"} else (),
                )
                self._agents.record_result(run_id, task_id, task_result)
                self._append_usage(run_id, task_id, result)
                if result.status not in {"success", "cancelled"}:
                    return self._interrupt(run_id, "provider_failure")
            if policy.maximum_total_cost is not None and spent > policy.maximum_total_cost:
                return self._interrupt(run_id, "budget_excess")
            if batch != batches[-1]:
                return self._interrupt(run_id, "integration_approval")
        self._save_cursor(run_id, {"run_id": run_id, "interrupt": None})
        return {"run_id": run_id, "handoff": self._agents.handoff(run_id).model_dump(mode="json")}

    def resume(self, run_id: str, decision_path: str | Path) -> dict[str, object]:
        decision = json.loads(Path(decision_path).read_text(encoding="utf-8"))
        if not isinstance(decision, dict) or decision.get("action") != "continue":
            raise ValueError("decision must be an object with action 'continue'")
        cursor = self._load_cursor(run_id)
        policy_value = cursor.get("policy")
        if not isinstance(policy_value, dict):
            raise ValueError("run has no persisted provider policy")
        self._save_cursor(run_id, {"run_id": run_id, "interrupt": None, "policy": policy_value})
        return self._execute_with_policy(run_id, ProviderPolicy.model_validate(policy_value))

    def events(self, run_id: str, task_id: str | None = None) -> tuple[dict[str, object], ...]:
        path = self._events_path(run_id)
        if not path.exists():
            return ()
        values = tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line)
        return tuple(value for value in values if task_id is None or value.get("task_id") == task_id)

    def cancel(self, run_id: str, task_id: str | None = None) -> dict[str, object]:
        plan, _ = self._agents._load(run_id)
        targets = (task_id,) if task_id else tuple(task.task_id for task in plan.tasks)
        cancelled = tuple(target for target in targets if self._runtime.cancel(run_id, target))
        for target in targets:
            self._agents.record_result(run_id, target, AgentTaskResult(task_id=target, status="cancelled"))
        return {"run_id": run_id, "cancelled_tasks": cancelled, "handoff": self._agents.handoff(run_id).model_dump(mode="json")}

    def _dispatch(self, batch: tuple[object, ...], run_id: str) -> tuple[tuple[str, ProviderExecutionResult], ...]:
        def call(request: Any) -> tuple[str, ProviderExecutionResult]:
            return request.task_id, self._runtime.execute(request, event_sink=lambda event: self._append_event(run_id, request.task_id, event))
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            return tuple(executor.map(call, batch))

    def _interrupt(self, run_id: str, reason: str) -> dict[str, object]:
        self._save_cursor(run_id, {"run_id": run_id, "interrupt": reason})
        return {"run_id": run_id, "interrupt": reason, "handoff": self._agents.handoff(run_id).model_dump(mode="json")}

    def _append_event(self, run_id: str, task_id: str, event: ProviderEvent) -> None:
        path = self._events_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        value = {"task_id": task_id, **_sanitize(event.model_dump(mode="json"))}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, sort_keys=True) + "\n")

    def _append_usage(self, run_id: str, task_id: str, result: ProviderExecutionResult) -> None:
        path = self._usage_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"task_id": task_id, "usage": result.usage.model_dump(mode="json")}, sort_keys=True) + "\n")

    def _spent(self, run_id: str) -> float:
        path = self._usage_path(run_id)
        if not path.exists(): return 0.0
        return sum(float(json.loads(line)["usage"]["estimated_cost"]) for line in path.read_text(encoding="utf-8").splitlines() if line)

    def _load_cursor(self, run_id: str) -> dict[str, object]:
        path = self._cursor_path(run_id)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"run_id": run_id, "interrupt": None}

    def _save_cursor(self, run_id: str, value: dict[str, object]) -> None:
        cursor = LangGraphOrchestrator.cursor(
            run_id,
            dispatched_task_ids=tuple(value.get("dispatched_task_ids", ())),
            interrupt=value.get("interrupt") if isinstance(value.get("interrupt"), str) else None,
        )
        value = {**value, "cursor": {"run_id": cursor.run_id, "dispatched_task_ids": cursor.dispatched_task_ids, "interrupt": cursor.interrupt}}
        path = self._cursor_path(run_id); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    def _cursor_path(self, run_id: str) -> Path: return self._agents.state_root / "provider-cursors" / f"{run_id}.json"
    def _events_path(self, run_id: str) -> Path: return self._agents.state_root / "provider-events" / f"{run_id}.jsonl"
    def _usage_path(self, run_id: str) -> Path: return self._agents.state_root / "provider-usage" / f"{run_id}.jsonl"


def _sanitize(value: object) -> object:
    if isinstance(value, dict): return {key: "[redacted]" if any(token in key.lower() for token in _SECRET_KEYS) else _sanitize(item) for key, item in value.items()}
    if isinstance(value, list): return [_sanitize(item) for item in value]
    return value
