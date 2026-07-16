from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, ApplicationIntent

def compile_plan(intent: ApplicationIntent, *, run_id: str | None = None, maximum_parallel_tasks: int = 1) -> AgentRunPlan:
    task = AgentTask(task_id=intent.intent_id, role="implementation", objective=intent.objective, allowed_paths=(".",), required_context=("AGENTS.md",), expected_outputs=("implementation",), verification_commands=())
    return AgentRunPlan(run_id=run_id or f"run-{intent.intent_id}", intent=intent, tasks=(task,), maximum_parallel_tasks=maximum_parallel_tasks)
