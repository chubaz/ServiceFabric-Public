"""Deterministic compilation of application intents into agent run plans."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath

from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, ApplicationIntent


class PlanValidationError(ValueError):
    """Raised when task input cannot form a safe, executable plan."""


def _default_task(intent: ApplicationIntent) -> AgentTask:
    return AgentTask(
        task_id=intent.intent_id,
        role="implementation",
        objective=intent.objective,
        allowed_paths=(".",),
        required_context=("AGENTS.md",),
        expected_outputs=("implementation",),
        verification_commands=(),
    )


def _validate_path(path: str, *, task_id: str, field: str) -> None:
    candidate = PurePosixPath(path)
    if not path or path.startswith("/") or "\\" in path or ".." in candidate.parts:
        raise PlanValidationError(
            f"task {task_id!r} has unsafe {field} entry {path!r}; "
            "repository paths must be relative and may not traverse parents"
        )


def _validate_tasks(tasks: tuple[AgentTask, ...]) -> None:
    if not tasks:
        raise PlanValidationError("a plan must contain at least one task")

    task_ids = tuple(task.task_id for task in tasks)
    known_ids = set(task_ids)
    if len(known_ids) != len(task_ids):
        duplicate = next(task_id for task_id in task_ids if task_ids.count(task_id) > 1)
        raise PlanValidationError(f"duplicate task_id {duplicate!r}")

    dependencies: dict[str, tuple[str, ...]] = {}
    for task in tasks:
        if not task.allowed_paths:
            raise PlanValidationError(f"task {task.task_id!r} must declare allowed_paths")
        for field in ("allowed_paths", "forbidden_paths"):
            for path in getattr(task, field):
                _validate_path(path, task_id=task.task_id, field=field)

        unknown = set(task.dependencies) - known_ids
        if unknown:
            rendered = ", ".join(sorted(unknown))
            raise PlanValidationError(
                f"task {task.task_id!r} has unknown dependencies: {rendered}"
            )
        if task.task_id in task.dependencies:
            raise PlanValidationError(f"task {task.task_id!r} cannot depend on itself")
        dependencies[task.task_id] = task.dependencies

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise PlanValidationError(f"task dependency cycle includes {task_id!r}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in dependencies[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in task_ids:
        visit(task_id)


def compile_plan(
    intent: ApplicationIntent,
    *,
    run_id: str | None = None,
    maximum_parallel_tasks: int = 1,
    tasks: Iterable[AgentTask] | None = None,
) -> AgentRunPlan:
    """Compile an intent and bounded task graph into an immutable run plan.

    When no tasks are supplied, a backwards-compatible implementation task is
    created. Supplying tasks lets callers describe independent work and explicit
    dependencies without putting provider or execution behavior in the planner.
    """

    compiled_tasks = (_default_task(intent),) if tasks is None else tuple(tasks)
    _validate_tasks(compiled_tasks)
    return AgentRunPlan(
        run_id=run_id or f"run-{intent.intent_id}",
        intent=intent,
        tasks=compiled_tasks,
        maximum_parallel_tasks=maximum_parallel_tasks,
    )
