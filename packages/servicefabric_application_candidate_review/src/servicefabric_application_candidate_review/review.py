"""Candidate review uses bounded, read-only Git inspection only."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from servicefabric_agentic_contracts import AgentTask, AgentTaskResult
from servicefabric_application_factory_contracts import CandidateReviewDecision


@dataclass(frozen=True)
class GitCandidateInspector:
    """Read candidate commit metadata without altering its repository."""

    repository: Path

    def resolve_commit_object(self, candidate: str) -> str:
        if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate):
            raise ValueError("candidate identity must be a full lowercase hexadecimal commit SHA")
        resolved = self._git("rev-parse", "--verify", f"{candidate}^{{commit}}").strip()
        if resolved != candidate:
            raise ValueError("candidate identity must equal its canonical commit SHA")
        return resolved

    def changed_paths(self, commit_sha: str) -> tuple[str, ...]:
        output = self._git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit_sha)
        return tuple(path for path in output.splitlines() if path)

    def is_merge_commit(self, commit_sha: str) -> bool:
        parents = self._git("rev-list", "--parents", "-n", "1", commit_sha).split()
        return len(parents) > 2

    def _git(self, *arguments: str) -> str:
        try:
            completed = subprocess.run(
                ("git", "-C", str(self.repository), *arguments),
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError("candidate commit could not be inspected with read-only Git") from error
        return completed.stdout


class CandidateReviewService:
    """Convert task evidence and an inspected candidate commit into one decision."""

    def review(
        self,
        *,
        decision_id: str,
        run_id: str,
        task: AgentTask,
        task_result: AgentTaskResult,
        repository: str | Path,
        decided_by: str,
    ) -> CandidateReviewDecision:
        inspector = GitCandidateInspector(Path(repository))
        reasons: list[str] = []
        actual_paths: tuple[str, ...] = ()
        commit_sha = task_result.commit_sha or ""

        try:
            commit_sha = inspector.resolve_commit_object(commit_sha)
            actual_paths = inspector.changed_paths(commit_sha)
            if inspector.is_merge_commit(commit_sha):
                reasons.append("candidate commit must not be a merge commit")
        except ValueError:
            raise ValueError("candidate identity is not an immutable inspectable commit SHA") from None

        if task_result.task_id != task.task_id:
            reasons.append("task result does not belong to the reviewed task")
        if task_result.status != "success":
            reasons.append(f"task result status is {task_result.status}")
        if tuple(task_result.changed_paths) != actual_paths:
            reasons.append("reported changed paths do not match the candidate commit")
        if not task_result.evidence:
            reasons.append("candidate has no verification evidence")
        elif any(item.exit_code != 0 for item in task_result.evidence):
            reasons.append("candidate verification evidence contains a failure")
        if task_result.blockers:
            reasons.append("candidate reports unresolved blockers")
        if any(not self._is_owned_path(path, task.allowed_paths) for path in actual_paths):
            reasons.append("candidate changes a path outside the task allowlist")
        if any(self._is_owned_path(path, task.forbidden_paths) for path in actual_paths):
            reasons.append("candidate changes a forbidden path")

        decision = "accept" if not reasons else self._non_accepting_decision(task_result)
        reason = "candidate commit, paths, and verification evidence satisfy the task" if not reasons else "; ".join(reasons)
        return CandidateReviewDecision(
            decision_id=decision_id,
            run_id=run_id,
            task_id=task.task_id,
            commit_sha=commit_sha,
            decision=decision,
            reason=reason,
            changed_paths=actual_paths,
            evidence_refs=tuple(
                item.artifact_ref for item in task_result.evidence if item.artifact_ref is not None
            ),
        )

    @staticmethod
    def _non_accepting_decision(task_result: AgentTaskResult) -> str:
        if task_result.status in {"blocked", "cancelled"}:
            return "escalate"
        return "rework"

    @staticmethod
    def _is_owned_path(path: str, roots: tuple[str, ...]) -> bool:
        normalized_path = path.strip("/")
        return any(
            normalized_path == root.strip("/") or normalized_path.startswith(root.strip("/") + "/")
            for root in roots
        )
