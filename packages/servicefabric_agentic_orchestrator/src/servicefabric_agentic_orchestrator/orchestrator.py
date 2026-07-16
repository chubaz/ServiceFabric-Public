"""Deterministic scheduling decisions for an agent run plan."""

from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, AgentTaskResult


_IN_FLIGHT_STATUSES = frozenset({"pending", "running"})


def ready_tasks(
    plan: AgentRunPlan,
    results: tuple[AgentTaskResult, ...] = (),
) -> tuple[AgentTask, ...]:
    """Return the next dependency-satisfied tasks within the run's capacity.

    A recorded task is never dispatched a second time. Pending and running tasks
    reserve parallel capacity, while results for task IDs outside this plan are
    ignored. Tasks are returned in plan order to keep scheduling reproducible.
    """

    task_ids = {task.task_id for task in plan.tasks}
    statuses = {
        result.task_id: result.status
        for result in results
        if result.task_id in task_ids
    }
    in_flight = sum(
        status in _IN_FLIGHT_STATUSES for status in statuses.values()
    )
    available_slots = max(0, plan.maximum_parallel_tasks - in_flight)
    if available_slots == 0:
        return ()

    ready: list[AgentTask] = []
    scheduled_ids: set[str] = set()
    for task in plan.tasks:
        if task.task_id in statuses or task.task_id in scheduled_ids:
            continue
        dependencies_succeeded = all(
            statuses.get(dependency) == "success"
            for dependency in task.dependencies
        )
        if dependencies_succeeded:
            ready.append(task)
            scheduled_ids.add(task.task_id)
            if len(ready) == available_slots:
                break

    return tuple(ready)
