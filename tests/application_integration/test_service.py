from __future__ import annotations

import unittest

from servicefabric_application_factory_contracts import CandidateReviewDecision
from servicefabric_application_integration import (
    ApplicationIntegrationRequest,
    ApplicationIntegrationService,
    VerificationOutcome,
)


class FakeRepository:
    def __init__(self, available: tuple[str, ...] = ("a" * 40,)) -> None:
        self.available = set(available)
        self.applied: list[tuple[str, str]] = []
        self.verification = VerificationOutcome(succeeded=True, evidence_refs=("evidence/verify",))
        self.clean, self.branch, self.head = True, "integration/app-1", "b" * 40
        self.paths: tuple[str, ...] = ()
        self.ancestor, self.already_integrated = True, False

    def is_clean(self) -> bool:
        return self.clean

    def current_branch(self) -> str:
        return self.branch

    def head_sha(self) -> str:
        return self.head

    def commit_exists(self, commit_sha: str) -> bool:
        return commit_sha in self.available

    def changed_paths(self, commit_sha: str, base_sha: str) -> tuple[str, ...]:
        return self.paths

    def is_ancestor(self, ancestor_sha: str, descendant_sha: str) -> bool:
        return self.ancestor

    def is_already_integrated(self, commit_sha: str) -> bool:
        return self.already_integrated

    def cherry_pick_exact(self, *, commit_sha: str, target_branch: str) -> str:
        self.applied.append((commit_sha, target_branch))
        return "c" * 40

    def integration_commit(self, *, target_branch: str) -> str:
        return "b" * 40

    def run_verification(self, commands: tuple[str, ...]) -> VerificationOutcome:
        self.commands = commands
        return self.verification


def decision(*, task_id: str = "api", outcome: str = "accept") -> CandidateReviewDecision:
    return CandidateReviewDecision(
        decision_id=f"review-{task_id}", run_id="run-1", task_id=task_id,
        commit_sha="a" * 40, decision=outcome, reason="reviewed",
    )


def request(**changes: object) -> ApplicationIntegrationRequest:
    values: dict[str, object] = {
        "run_id": "run-1", "application_id": "app-1", "integration_branch": "integration/app-1",
        "required_task_ids": ("api",), "review_decisions": (decision(),),
        "verification_commands": ("make verify",), "agent_handoff_ref": "handoffs/run-1",
        "expected_head": "b" * 40, "allowed_verification_commands": ("make verify",),
    }
    values.update(changes)
    return ApplicationIntegrationRequest(**values)  # type: ignore[arg-type]


class ApplicationIntegrationTests(unittest.TestCase):
    def test_applies_only_accepted_exact_commit_then_returns_evidence(self) -> None:
        repository = FakeRepository()
        handoff = ApplicationIntegrationService().integrate(request(), repository)
        self.assertEqual(handoff.status, "success")
        self.assertEqual(repository.applied, [("a" * 40, "integration/app-1")])
        self.assertEqual(handoff.verification_evidence, ("evidence/verify",))

    def test_missing_or_non_accepted_review_blocks_without_applying(self) -> None:
        for reviews in ((), (decision(outcome="rework"),)):
            with self.subTest(reviews=reviews):
                repository = FakeRepository()
                handoff = ApplicationIntegrationService().integrate(request(review_decisions=reviews), repository)
                self.assertEqual(handoff.status, "blocked")
                self.assertEqual(repository.applied, [])

    def test_never_integrates_main_or_unavailable_commit(self) -> None:
        for integration_request, repository in (
            (request(integration_branch="main"), FakeRepository()),
            (request(), FakeRepository(available=())),
        ):
            with self.subTest(branch=integration_request.integration_branch):
                handoff = ApplicationIntegrationService().integrate(integration_request, repository)
                self.assertEqual(handoff.status, "blocked")
                self.assertEqual(repository.applied, [])

    def test_failed_verification_returns_failed_handoff_with_evidence(self) -> None:
        repository = FakeRepository()
        repository.verification = VerificationOutcome(False, ("evidence/failed",))
        handoff = ApplicationIntegrationService().integrate(request(), repository)
        self.assertEqual(handoff.status, "failed")
        self.assertEqual(handoff.verification_evidence, ("evidence/failed",))

    def test_rejects_repository_safety_mismatches_before_mutation(self) -> None:
        cases = (
            lambda repo, values: setattr(repo, "clean", False),
            lambda repo, values: setattr(repo, "branch", "feature/x"),
            lambda repo, values: setattr(repo, "head", "c" * 40),
            lambda repo, values: values.update(superseded_candidate_shas=("a" * 40,)),
            lambda repo, values: setattr(repo, "paths", ("other.py",)),
            lambda repo, values: setattr(repo, "already_integrated", True),
            lambda repo, values: values.update(verification_commands=("unsafe",)),
        )
        for configure in cases:
            with self.subTest(configure=configure):
                repository, values = FakeRepository(), {}
                configure(repository, values)
                handoff = ApplicationIntegrationService().integrate(request(**values), repository)
                self.assertEqual("blocked", handoff.status)
                self.assertEqual([], repository.applied)
