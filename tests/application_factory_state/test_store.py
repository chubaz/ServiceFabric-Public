import json
import tempfile
import unittest
from pathlib import Path

from servicefabric_application_factory_contracts import (
    ApplicationFactoryHandoff,
    CandidateReviewDecision,
    FactoryApprovalDecision,
    UnmetRequirement,
)
from servicefabric_application_factory_state import FileFactoryLifecycleStore


RUN_ID = "factory-run"
APPLICATION_ID = "example-app"


def approval() -> FactoryApprovalDecision:
    return FactoryApprovalDecision(
        decision_id="approval-one",
        run_id=RUN_ID,
        subject_ref="engineering-blueprint:one",
        decision="approve",
        reason="reviewed profile and blueprint",
        decided_by="factory-approver",
        evidence_refs=("evidence:blueprint",),
    )


def review() -> CandidateReviewDecision:
    return CandidateReviewDecision(
        decision_id="review-one",
        run_id=RUN_ID,
        task_id="implementation",
        commit_sha="abcdef1",
        decision="accept",
        reason="verification passed",
        changed_paths=("src/example.py",),
        evidence_refs=("evidence:verification",),
    )


def requirement() -> UnmetRequirement:
    return UnmetRequirement(
        requirement_id="requirement-one",
        application_id=APPLICATION_ID,
        run_id=RUN_ID,
        originating_task_id="implementation",
        required_behavior="Support a required external integration.",
        evidence_refs=("evidence:gap",),
        proposed_scope="framework-kit",
        urgency="high",
    )


def handoff() -> ApplicationFactoryHandoff:
    return ApplicationFactoryHandoff(
        run_id=RUN_ID,
        application_id=APPLICATION_ID,
        status="blocked",
        agent_handoff_ref="handoffs/factory-run.md",
        review_decision_refs=("review-one",),
        unmet_requirements=(requirement(),),
        verification_evidence=("evidence:verification",),
    )


class FileFactoryLifecycleStoreTests(unittest.TestCase):
    def test_persists_only_factory_lifecycle_records(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileFactoryLifecycleStore(root)
            store.record_approval(approval())
            store.record_review(review())
            store.record_unmet_requirement(requirement())
            store.record_handoff(handoff())

            snapshot = FileFactoryLifecycleStore(root).load(RUN_ID)
            self.assertEqual(snapshot.approvals, (approval(),))
            self.assertEqual(snapshot.reviews, (review(),))
            self.assertEqual(snapshot.unmet_requirements, (requirement(),))
            self.assertEqual(snapshot.handoff, handoff())

            state = json.loads(Path(root, f"{RUN_ID}.json").read_text(encoding="utf-8"))
            self.assertEqual(
                set(state), {"approvals", "handoff", "reviews", "unmet_requirements"}
            )

    def test_records_are_idempotent_but_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileFactoryLifecycleStore(root)
            store.record_approval(approval())
            store.record_approval(approval())
            replacement = approval().model_copy(update={"decision": "reject"})
            with self.assertRaisesRegex(ValueError, "different approvals record"):
                store.record_approval(replacement)

            store.record_handoff(handoff())
            with self.assertRaisesRegex(ValueError, "different handoff"):
                store.record_handoff(handoff().model_copy(update={"status": "failed"}))

    def test_rejects_mismatched_handoff_and_corrupt_state(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileFactoryLifecycleStore(root)
            wrong_requirement = requirement().model_copy(update={"run_id": "other-run"})
            invalid_handoff = handoff().model_copy(
                update={"unmet_requirements": (wrong_requirement,)}
            )
            with self.assertRaisesRegex(ValueError, "must belong"):
                store.record_handoff(invalid_handoff)

            store.record_review(review())
            state_path = Path(root, f"{RUN_ID}.json")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["reviews"]["review-one"]["run_id"] = "other-run"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid review record"):
                store.load(RUN_ID)

    def test_rejects_unsafe_run_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileFactoryLifecycleStore(root)
            with self.assertRaisesRegex(ValueError, "invalid run_id"):
                store.load("../outside")


if __name__ == "__main__":
    unittest.main()
