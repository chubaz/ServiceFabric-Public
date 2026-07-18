"""Bounded integration authority; Git transport is supplied by an adapter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from servicefabric_application_factory_contracts import (
    ApplicationFactoryHandoff,
    CandidateReviewDecision,
    UnmetRequirement,
)


@dataclass(frozen=True, slots=True)
class ApplicationIntegrationRequest:
    """The approved application closure inputs for one factory run."""

    run_id: str
    application_id: str
    integration_branch: str
    required_task_ids: tuple[str, ...]
    review_decisions: tuple[CandidateReviewDecision, ...]
    verification_commands: tuple[str, ...]
    agent_handoff_ref: str
    expected_head: str = ""
    allowed_verification_commands: tuple[str, ...] = ()
    superseded_candidate_shas: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationOutcome:
    """Evidence emitted by the integration-owned verification boundary."""

    succeeded: bool
    evidence_refs: tuple[str, ...] = ()


class IntegrationRepository(Protocol):
    """Adapter boundary for exact, non-destructive repository operations."""

    def is_clean(self) -> bool: ...
    def current_branch(self) -> str: ...
    def head_sha(self) -> str: ...
    def commit_exists(self, commit_sha: str) -> bool: ...
    def changed_paths(self, commit_sha: str, base_sha: str) -> tuple[str, ...]: ...
    def is_ancestor(self, ancestor_sha: str, descendant_sha: str) -> bool: ...
    def is_already_integrated(self, commit_sha: str) -> bool: ...

    def cherry_pick_exact(self, *, commit_sha: str, target_branch: str) -> str: ...

    def integration_commit(self, *, target_branch: str) -> str: ...

    def run_verification(self, commands: tuple[str, ...]) -> VerificationOutcome: ...


class ApplicationIntegrationService:
    """Applies reviewed candidates and returns a structured factory handoff."""

    def integrate(
        self,
        request: ApplicationIntegrationRequest,
        repository: IntegrationRepository,
    ) -> ApplicationFactoryHandoff:
        if request.integration_branch == "main":
            return self._blocked(request, "Integration into main is not automatic.")
        if not repository.is_clean():
            return self._blocked(request, "Repository must be clean before integration.")
        if repository.current_branch() != request.integration_branch:
            return self._blocked(request, "Repository is not on the approved integration branch.")
        if not request.expected_head or repository.head_sha() != request.expected_head:
            return self._blocked(request, "Integration branch differs from the approved baseline.")
        if request.allowed_verification_commands and any(
            command not in request.allowed_verification_commands
            for command in request.verification_commands
        ):
            return self._blocked(request, "Verification command is not declared by the integration plan.")

        decisions_by_task = self._decisions_by_task(request.review_decisions)
        missing = tuple(task_id for task_id in request.required_task_ids if task_id not in decisions_by_task)
        if missing:
            return self._blocked(request, f"Required candidate reviews are missing: {', '.join(missing)}.")

        rejected = tuple(
            task_id
            for task_id in request.required_task_ids
            if decisions_by_task[task_id].decision != "accept"
        )
        if rejected:
            return self._blocked(request, f"Required candidates are not accepted: {', '.join(rejected)}.")

        accepted = tuple(decisions_by_task[task_id] for task_id in request.required_task_ids)
        unavailable = tuple(
            decision.task_id
            for decision in accepted
            if not repository.commit_exists(decision.commit_sha)
        )
        if unavailable:
            return self._blocked(request, f"Accepted exact commits are unavailable: {', '.join(unavailable)}.")

        for decision in accepted:
            if decision.commit_sha in request.superseded_candidate_shas:
                return self._blocked(request, f"Accepted candidate is superseded: {decision.task_id}.")
            if repository.is_already_integrated(decision.commit_sha):
                return self._blocked(request, f"Candidate is already integrated: {decision.task_id}.")
            if not repository.is_ancestor(request.expected_head, decision.commit_sha):
                return self._blocked(request, f"Candidate is not applicable from the approved baseline: {decision.task_id}.")
            if repository.changed_paths(decision.commit_sha, request.expected_head) != decision.changed_paths:
                return self._blocked(request, f"Candidate paths differ from the accepted review: {decision.task_id}.")

        for decision in accepted:
            repository.cherry_pick_exact(
                commit_sha=decision.commit_sha,
                target_branch=request.integration_branch,
            )

        verification = repository.run_verification(request.verification_commands)
        if not verification.succeeded:
            return ApplicationFactoryHandoff(
                run_id=request.run_id,
                application_id=request.application_id,
                status="failed",
                integration_commit=repository.integration_commit(target_branch=request.integration_branch),
                agent_handoff_ref=request.agent_handoff_ref,
                review_decision_refs=tuple(decision.decision_id for decision in accepted),
                verification_evidence=verification.evidence_refs,
            )

        return ApplicationFactoryHandoff(
            run_id=request.run_id,
            application_id=request.application_id,
            status="success",
            integration_commit=repository.integration_commit(target_branch=request.integration_branch),
            agent_handoff_ref=request.agent_handoff_ref,
            review_decision_refs=tuple(decision.decision_id for decision in accepted),
            verification_evidence=verification.evidence_refs,
        )

    @staticmethod
    def _decisions_by_task(
        decisions: tuple[CandidateReviewDecision, ...],
    ) -> dict[str, CandidateReviewDecision]:
        by_task: dict[str, CandidateReviewDecision] = {}
        for decision in decisions:
            if decision.task_id in by_task:
                raise ValueError(f"Only one review decision is permitted for task {decision.task_id!r}.")
            by_task[decision.task_id] = decision
        return by_task

    @staticmethod
    def _blocked(
        request: ApplicationIntegrationRequest,
        reason: str,
    ) -> ApplicationFactoryHandoff:
        return ApplicationFactoryHandoff(
            run_id=request.run_id,
            application_id=request.application_id,
            status="blocked",
            agent_handoff_ref=request.agent_handoff_ref,
            unmet_requirements=(
                UnmetRequirement(
                    requirement_id=f"integration-{request.run_id}",
                    application_id=request.application_id,
                    run_id=request.run_id,
                    required_behavior=reason,
                    proposed_scope="application",
                    urgency="high",
                ),
            ),
        )
