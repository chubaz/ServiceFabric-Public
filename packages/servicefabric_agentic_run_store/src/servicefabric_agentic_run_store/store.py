"""Durable, provider-neutral storage for agent run state."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
from typing import Any, Iterator

from servicefabric_agentic_contracts import AgentHandoff, AgentRunPlan, AgentTaskResult


_RUN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class FileRunStore:
    """Persist plans and task results as one atomic JSON document per run."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def save_plan(self, plan: AgentRunPlan) -> None:
        """Create a run, or accept an idempotent save of the same plan."""
        with self._locked(plan.run_id):
            target = self._path(plan.run_id)
            if target.exists():
                state = self._load_state(plan.run_id)
                if state["plan"] != plan.model_dump(mode="json"):
                    raise ValueError(f"run {plan.run_id!r} already has a different plan")
                return
            self._write(
                plan.run_id,
                {"plan": plan.model_dump(mode="json"), "results": {}},
            )

    def load(self, run_id: str) -> dict[str, Any]:
        """Load and validate the persisted representation for a run."""
        return self._load_state(run_id)

    def record_result(self, run_id: str, result: AgentTaskResult) -> None:
        """Atomically add or replace a result belonging to the run's plan."""
        if result.task_id == "":  # Defensive; frozen contracts normally reject this.
            raise ValueError("task_id must not be empty")

        with self._locked(run_id):
            state = self._load_state(run_id)
            plan = AgentRunPlan.model_validate(state["plan"])
            task_ids = {task.task_id for task in plan.tasks}
            if result.task_id not in task_ids:
                raise ValueError(
                    f"task {result.task_id!r} does not belong to run {run_id!r}"
                )
            state["results"][result.task_id] = result.model_dump(mode="json")
            self._write(run_id, state)

    def handoff(self, run_id: str) -> AgentHandoff:
        """Build a deterministic handoff snapshot from durable run state."""
        state = self._load_state(run_id)
        plan = AgentRunPlan.model_validate(state["plan"])
        results_by_task = {
            task_id: AgentTaskResult.model_validate(value)
            for task_id, value in state["results"].items()
        }
        results = tuple(
            results_by_task[task.task_id]
            for task in plan.tasks
            if task.task_id in results_by_task
        )
        status = self._handoff_status(plan, results_by_task)
        blockers = tuple(blocker for item in results for blocker in item.blockers)
        return AgentHandoff(
            run_id=run_id,
            status=status,
            task_results=results,
            unresolved_blockers=blockers,
        )

    @staticmethod
    def _handoff_status(
        plan: AgentRunPlan,
        results: dict[str, AgentTaskResult],
    ) -> str:
        statuses = {result.status for result in results.values()}
        if "blocked" in statuses:
            return "blocked"
        if "failed" in statuses:
            return "failed"
        if "running" in statuses:
            return "running"

        complete = len(results) == len(plan.tasks)
        if complete and statuses == {"success"}:
            return "success"
        if complete and "cancelled" in statuses and statuses <= {"success", "cancelled"}:
            return "cancelled"
        if statuses.intersection({"success", "cancelled"}):
            return "running"
        return "pending"

    def _path(self, run_id: str) -> Path:
        if not _RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError(f"invalid run_id: {run_id!r}")
        return self.root / f"{run_id}.json"

    def _load_state(self, run_id: str) -> dict[str, Any]:
        value = json.loads(self._path(run_id).read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != {"plan", "results"}:
            raise ValueError(f"invalid state for run {run_id!r}")

        plan = AgentRunPlan.model_validate(value["plan"])
        if plan.run_id != run_id:
            raise ValueError(
                f"stored plan id {plan.run_id!r} does not match run {run_id!r}"
            )
        if not isinstance(value["results"], dict):
            raise ValueError(f"invalid results for run {run_id!r}")

        task_ids = {task.task_id for task in plan.tasks}
        for task_id, result_value in value["results"].items():
            result = AgentTaskResult.model_validate(result_value)
            if task_id != result.task_id or task_id not in task_ids:
                raise ValueError(f"invalid result task {task_id!r} for run {run_id!r}")
        return value

    @contextmanager
    def _locked(self, run_id: str) -> Iterator[None]:
        target = self._path(run_id)
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = target.with_suffix(".lock")
        with lock_path.open("a+b") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _write(self, run_id: str, value: dict[str, Any]) -> None:
        target = self._path(run_id)
        temp = target.with_suffix(".tmp")
        try:
            with temp.open("w", encoding="utf-8") as temp_file:
                json.dump(value, temp_file, sort_keys=True, indent=2)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp, target)
            directory_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temp.unlink(missing_ok=True)
