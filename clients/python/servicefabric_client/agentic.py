"""CLI composition for provider-neutral Wave-7 planning state."""
from __future__ import annotations
import json
from pathlib import Path
from servicefabric_agent_harness import CodexPromptHarness
from servicefabric_agentic_contracts import AgentTaskResult, ApplicationIntent, VerificationEvidence
from servicefabric_agentic_orchestrator import ready_tasks
from servicefabric_agentic_planner import compile_plan
from servicefabric_agentic_run_store import FileRunStore

def _store(repository: str | None) -> FileRunStore:
    root = Path(repository or ".").resolve()
    return FileRunStore(root / ".agent-runs" / "wave-07")

def dispatch_agents(args: object) -> tuple[int, str, object]:
    command = args.agents_action
    if command == "plan":
        raw = json.loads(Path(args.intent).read_text(encoding="utf-8"))
        intent = ApplicationIntent.model_validate(raw)
        plan = compile_plan(intent, maximum_parallel_tasks=args.maximum_parallel_tasks)
        store = _store(args.repository); store.save_plan(plan)
        return 0, "agents-plan", plan.model_dump(mode="json")
    store = _store(getattr(args, "repository", None))
    state = store.load(args.run_id)
    from servicefabric_agentic_contracts import AgentRunPlan
    plan = AgentRunPlan.model_validate(state["plan"])
    if command == "prepare":
        return 0, "agents-prepare", {"run_id": plan.run_id, "repository": str(Path(args.repository).resolve()), "tasks": [CodexPromptHarness().prepare_task(task, args.repository) for task in plan.tasks]}
    if command == "ready":
        results = tuple(AgentTaskResult.model_validate(value) for value in state["results"].values())
        return 0, "agents-ready", {"run_id": plan.run_id, "tasks": [item.model_dump(mode="json") for item in ready_tasks(plan, results)]}
    if command == "render":
        if args.harness != "codex": raise ValueError("only the provider-neutral codex prompt exporter is available")
        harness = CodexPromptHarness()
        return 0, "agents-render", {"run_id": plan.run_id, "prompts": {task.task_id: harness.render_task(task) for task in plan.tasks}}
    if command == "record-result":
        result = AgentTaskResult.model_validate(json.loads(Path(args.result).read_text(encoding="utf-8")))
        if result.task_id != args.task_id:
            raise ValueError("result task_id does not match TASK_ID")
        if result.task_id not in {task.task_id for task in plan.tasks}: raise ValueError("result task_id is not part of the run")
        store.record_result(plan.run_id, result); return 0, "agents-record-result", result.model_dump(mode="json")
    handoff = store.handoff(plan.run_id)
    if command == "verify":
        failed = [item.task_id for item in handoff.task_results if any(e.exit_code for e in item.evidence)]
        return (1 if failed else 0), "agents-verify", {"run_id": plan.run_id, "valid": not failed, "failed_tasks": failed}
    return 0, "agents-handoff" if command == "handoff" else "agents-status", handoff.model_dump(mode="json")
