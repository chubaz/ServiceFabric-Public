from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from servicefabric_application_factory_contracts import ModuleTechnologySelection, TechnologyProfile
from servicefabric_distillation_contracts import ApplicationEvidenceBundle, DistillationDecision, TechniquePolicyDefinition
from servicefabric_technique_policies import (
    TechniquePolicyCatalog,
    TechniquePolicyConflictError,
    TechniquePolicyPublicationError,
    candidate_from_profile_and_evidence,
)


def policy(version: str = "1.0.0", techniques: tuple[str, ...] = ("structured-output",)) -> TechniquePolicyDefinition:
    return TechniquePolicyDefinition(policy_id="python.web", version=version, approved_techniques=techniques)


def profile(approved: bool = True) -> TechnologyProfile:
    return TechnologyProfile(
        profile_id="text-utility-profile", application_blueprint_id="text-utility", application_blueprint_version="1.0.0", approved=approved,
        module_selections=(ModuleTechnologySelection(module_id="api", primitive="http", kit_reference="fastapi@1.0.0", adapter_id="fastapi", runtime_family="python", technique_policy_ids=("python.web",), provider_role="implementation"),),
    )


def evidence(**overrides: object) -> ApplicationEvidenceBundle:
    value = {"bundle_id": "text-utility-evidence", "application_id": "text-utility", "repository_head": "abcdef1", "application_blueprint_id": "text-utility", "technology_profile_id": "text-utility-profile", "verification_evidence_refs": ("test:passing",), "review_decision_refs": ("review:accepted",)}
    value.update(overrides)
    return ApplicationEvidenceBundle(**value)


def approval(candidate_id: str) -> DistillationDecision:
    return DistillationDecision(decision_id="policy-review", candidate_ref=candidate_id, decision="approve", reason="Reviewed", decided_by="reviewer")


class TechniquePolicyCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.catalog = TechniquePolicyCatalog(Path(self.temporary.name) / "catalog")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_candidate_is_deterministic_from_approved_profile_and_successful_evidence(self) -> None:
        first = candidate_from_profile_and_evidence(policy(), profile(), evidence())
        second = candidate_from_profile_and_evidence(policy(), profile(), evidence())
        self.assertEqual(first, second)
        self.assertEqual(first.status, "proposed")
        self.assertEqual(first.evidence_refs, ("review:accepted", "test:passing"))

    def test_publish_is_exact_version_idempotent_and_deterministic(self) -> None:
        candidate = candidate_from_profile_and_evidence(policy(), profile(), evidence())
        first = self.catalog.publish(candidate, approval(candidate.candidate_id), profile(), evidence())
        second = self.catalog.publish(candidate, approval(candidate.candidate_id), profile(), evidence())
        self.assertEqual(first, second)
        self.assertEqual(self.catalog.describe("python.web", "1.0.0"), first)
        self.assertEqual(self.catalog.list("python.web"), (first,))

    def test_conflicting_exact_version_is_rejected_without_overwrite(self) -> None:
        candidate = candidate_from_profile_and_evidence(policy(), profile(), evidence())
        published = self.catalog.publish(candidate, approval(candidate.candidate_id), profile(), evidence())
        changed = candidate_from_profile_and_evidence(policy(techniques=("different",)), profile(), evidence())
        with self.assertRaises(TechniquePolicyConflictError):
            self.catalog.publish(changed, approval(changed.candidate_id), profile(), evidence())
        self.assertEqual(self.catalog.describe("python.web", "1.0.0"), published)

    def test_rejects_unapproved_profile_unsuccessful_evidence_and_nonapproval(self) -> None:
        with self.assertRaises(TechniquePolicyPublicationError):
            candidate_from_profile_and_evidence(policy(), profile(approved=False), evidence())
        with self.assertRaises(TechniquePolicyPublicationError):
            candidate_from_profile_and_evidence(policy(), profile(), evidence(verification_evidence_refs=()))
        candidate = candidate_from_profile_and_evidence(policy(), profile(), evidence())
        denied = approval(candidate.candidate_id).model_copy(update={"decision": "reject"})
        with self.assertRaises(TechniquePolicyPublicationError):
            self.catalog.publish(candidate, denied, profile(), evidence())


if __name__ == "__main__":
    unittest.main()
