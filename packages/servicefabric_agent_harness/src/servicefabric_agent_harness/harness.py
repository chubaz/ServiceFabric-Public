"""Provider-neutral preparation of coding-agent task prompts."""

from __future__ import annotations

from pathlib import Path

from servicefabric_agentic_contracts import AgentTask, AgentTaskResult


class CodexPromptHarness:
    """Export deterministic task packs without invoking a model provider."""

    def __init__(self) -> None:
        self._results: dict[str, AgentTaskResult] = {}

    def prepare_task(self, task: AgentTask, repository: str) -> dict[str, str]:
        """Return the portable inputs needed to hand a task to Codex."""
        repository_path = Path(repository).expanduser().resolve()
        self._results.setdefault(
            task.task_id,
            AgentTaskResult(task_id=task.task_id, status="pending"),
        )
        return {
            "task_id": task.task_id,
            "repository": str(repository_path),
            "prompt": self.render_task(task),
        }

    def render_task(self, task: AgentTask) -> str:
        """Render all scheduling, ownership, context, and verification bounds."""
        sections = (
            ("Task", (task.task_id,)),
            ("Role", (task.role,)),
            ("Objective", (task.objective,)),
            ("Dependencies", task.dependencies),
            ("Allowed paths", task.allowed_paths),
            ("Forbidden paths", task.forbidden_paths),
            ("Required context", task.required_context),
            ("Expected outputs", task.expected_outputs),
            ("Verification", task.verification_commands),
        )
        lines = [
            "Execute the bounded coding task below.",
            "Work only within the allowed paths and do not modify forbidden paths.",
        ]
        lines.extend(
            f"{heading}: {', '.join(values) if values else '(none)'}"
            for heading, values in sections
        )
        return "\n".join(lines) + "\n"

    def launch_task(self, task: AgentTask) -> str:
        """Mark a task prepared; provider execution is outside this harness."""
        self._results.setdefault(
            task.task_id,
            AgentTaskResult(task_id=task.task_id, status="pending"),
        )
        return f"prepared:{task.task_id}"

    def collect_result(self, task_id: str) -> AgentTaskResult:
        """Return locally tracked state for a prepared or cancelled task."""
        return self._results[task_id]

    def cancel_task(self, task_id: str) -> None:
        """Record a deterministic cancellation result."""
        self._results[task_id] = AgentTaskResult(
            task_id=task_id,
            status="cancelled",
        )
