from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, AgentTaskResult

def ready_tasks(plan: AgentRunPlan, results: tuple[AgentTaskResult, ...] = ()) -> tuple[AgentTask, ...]:
    status = {item.task_id: item.status for item in results}
    ready = tuple(task for task in plan.tasks if task.task_id not in status and all(status.get(dep) == "success" for dep in task.dependencies))
    return ready[:plan.maximum_parallel_tasks]
