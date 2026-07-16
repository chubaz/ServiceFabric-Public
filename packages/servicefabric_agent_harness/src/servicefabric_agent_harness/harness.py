from __future__ import annotations
from pathlib import Path
from servicefabric_agentic_contracts import AgentTask, AgentTaskResult

class CodexPromptHarness:
    """Exports deterministic task prompts; it never invokes a model provider."""
    def __init__(self): self._results: dict[str, AgentTaskResult] = {}
    def prepare_task(self, task: AgentTask, repository: str) -> dict[str, str]: return {"task_id": task.task_id, "repository": str(Path(repository).resolve())}
    def render_task(self, task: AgentTask) -> str:
        return "\n".join((f"Task: {task.task_id}", f"Role: {task.role}", f"Objective: {task.objective}", f"Allowed paths: {', '.join(task.allowed_paths)}", f"Forbidden paths: {', '.join(task.forbidden_paths)}", f"Verification: {', '.join(task.verification_commands)}")) + "\n"
    def launch_task(self, task: AgentTask) -> str: return f"prepared:{task.task_id}"
    def collect_result(self, task_id: str) -> AgentTaskResult: return self._results[task_id]
    def cancel_task(self, task_id: str) -> None: self._results[task_id] = AgentTaskResult(task_id=task_id, status="cancelled")
