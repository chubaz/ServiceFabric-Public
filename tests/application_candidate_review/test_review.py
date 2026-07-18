from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from servicefabric_agentic_contracts import AgentTask, AgentTaskResult, VerificationEvidence
from servicefabric_application_candidate_review import CandidateReviewService


class CandidateReviewServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(tempfile.mkdtemp())
        self._git("init")
        self._git("config", "user.email", "reviewer@example.test")
        self._git("config", "user.name", "Candidate Reviewer")
        (self.repository / "src").mkdir()
        (self.repository / "src" / "feature.py").write_text("VALUE = 1\n")
        self._git("add", "src/feature.py")
        self._git("commit", "-m", "feat: candidate")
        self.commit_sha = self._git("rev-parse", "HEAD").strip()
        self.task = AgentTask(
            task_id="feature",
            role="implementation",
            objective="Implement feature",
            allowed_paths=("src",),
            verification_commands=("python -m unittest",),
        )

    def test_accepts_inspected_successful_candidate(self) -> None:
        decision = self._review(self._result())
        self.assertEqual("accept", decision.decision)
        self.assertEqual(("src/feature.py",), decision.changed_paths)
        self.assertEqual(("artifacts/feature.txt",), decision.evidence_refs)

    def test_requires_reported_paths_to_match_commit(self) -> None:
        decision = self._review(self._result(changed_paths=("different.py",)))
        self.assertEqual("rework", decision.decision)
        self.assertIn("do not match", decision.reason)

    def test_rejects_mutable_or_noncanonical_candidate_identities(self) -> None:
        invalid = (None, "", " ", "HEAD", "main", "HEAD~1", self.commit_sha[:12], "g" * 40, "f" * 40)
        for commit_sha in invalid:
            with self.subTest(commit_sha=commit_sha):
                result = self._result().model_copy(update={"commit_sha": commit_sha})
                with self.assertRaisesRegex(ValueError, "immutable"):
                    self._review(result)

    def test_preserves_the_exact_full_commit_identity(self) -> None:
        decision = self._review(self._result())
        self.assertEqual(self.commit_sha, decision.commit_sha)

    def test_rejects_path_outside_lane_ownership(self) -> None:
        (self.repository / "README.md").write_text("outside lane\n")
        self._git("add", "README.md")
        self._git("commit", "-m", "docs: outside")
        commit_sha = self._git("rev-parse", "HEAD").strip()
        decision = self._review(self._result(commit_sha=commit_sha, changed_paths=("README.md",)))
        self.assertEqual("rework", decision.decision)
        self.assertIn("outside the task allowlist", decision.reason)

    def test_escalates_blocked_candidate(self) -> None:
        decision = self._review(self._result(status="blocked"))
        self.assertEqual("escalate", decision.decision)

    def _review(self, result: AgentTaskResult):
        return CandidateReviewService().review(
            decision_id="review-1",
            run_id="run-1",
            task=self.task,
            task_result=result,
            repository=self.repository,
            decided_by="reviewer",
        )

    def _result(
        self,
        *,
        commit_sha: str | None = None,
        changed_paths: tuple[str, ...] = ("src/feature.py",),
        status: str = "success",
    ) -> AgentTaskResult:
        return AgentTaskResult(
            task_id="feature",
            status=status,
            commit_sha=commit_sha or self.commit_sha,
            changed_paths=changed_paths,
            evidence=(VerificationEvidence(command="python -m unittest", exit_code=0, summary="passed", artifact_ref="artifacts/feature.txt"),),
        )

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
