from __future__ import annotations

import unittest

from servicefabric_capability_model import (
    CapabilityDefinition,
    CapabilityDefinitionSpec,
    CapabilityMetadata,
)
from servicefabric_contracts.effects import EffectContract, EffectDeclaration
from servicefabric_distillation_contracts import (
    ApplicationEvidenceBundle,
    BlueprintEvolutionProposal,
    CapabilityCandidate,
    DistillationDecision,
    DistillationReport,
    EngineeringPatternCandidate,
    SystemChangeProposal,
    TechniquePolicyCandidate,
    TechniquePolicyDefinition,
)


class DistillationContractTests(unittest.TestCase):
    def test_evidence_and_candidates_are_immutable_contracts(self) -> None:
        capability = CapabilityDefinition(
            api_version="servicefabric.local/v1",
            kind="CapabilityDefinition",
            metadata=CapabilityMetadata(id="notes.search", title="Search notes", domain="notes"),
            spec=CapabilityDefinitionSpec(
                operation_ref="notes.search",
                objective="Search reviewed notes",
                capability_class="retrieval",
                concepts=("notes",),
                expected_inputs=("query",),
                expected_outputs=("matches",),
                effect_contract=EffectContract(effects=(EffectDeclaration(
                    effect_type="external_read",
                    target_category="notes",
                    scope="reviewed notes",
                    reversibility="not_applicable",
                    verification_required=False,
                    approval_required=False,
                    idempotency_required=False,
                ),)),
            ),
        )
        bundle = ApplicationEvidenceBundle(
            bundle_id="bundle-1",
            application_id="notes",
            repository_head="abcdef0",
            application_blueprint_id="notes-blueprint",
            exact_manifest_refs=("manifest:notes",),
            content_digests={"manifest:notes": "sha256:" + "a" * 64},
        )
        candidate = CapabilityCandidate(
            candidate_id="capability-1",
            application_id="notes",
            operation_ref="notes.search",
            proposed_definition=capability,
            evidence_refs=("bundle:bundle-1",),
            rationale="Observed successful declared operation evidence.",
            confidence=1.0,
            status="proposed",
        )
        self.assertEqual(candidate.proposed_definition, capability)
        with self.assertRaises(Exception):
            bundle.application_id = "other"

    def test_policy_and_engineering_candidates_carry_bounded_references(self) -> None:
        policy = TechniquePolicyDefinition(
            policy_id="python-api",
            version="1.0.0",
            applicable_primitives=("service",),
            applicable_kit_refs=("fastapi-service@1.0.0",),
            approved_libraries=("fastapi==1.0.0",),
            approved_techniques=("dependency-injection",),
            prohibited_patterns=("global-mutable-state",),
            required_guidance=("guide:python-api",),
            verification_commands=("python3 -m unittest",),
            evidence_refs=("bundle:bundle-1",),
        )
        technique = TechniquePolicyCandidate(
            candidate_id="technique-1", proposed_definition=policy,
            evidence_refs=("bundle:bundle-1",), rationale="Successful reviewed profile.",
            confidence=0.9, status="proposed",
        )
        engineering = EngineeringPatternCandidate(
            candidate_id="pattern-1", source_blueprint_ref="engineering:notes@1.0.0",
            lane_topology=("implementation", "assurance"),
            provider_role_mapping={"implementation": "implementation"},
            path_ownership={"implementation": ("src",)},
            dependency_order=("implementation", "assurance"),
            verification_profile=("python3 -m unittest",),
            evidence_refs=("bundle:bundle-1",), status="proposed",
        )
        self.assertEqual(technique.proposed_definition.version, "1.0.0")
        self.assertEqual(engineering.dependency_order[-1], "assurance")

    def test_decisions_reports_and_proposals_are_non_executable_records(self) -> None:
        blueprint = BlueprintEvolutionProposal(
            proposal_id="blueprint-1", blueprint_id="notes-blueprint", blueprint_version="1.0.0",
            category="verification", required_behavior="Declare a smoke command.",
            evidence_refs=("evidence:verification",), proposed_change="Add declarative verification guidance.",
            status="proposed",
        )
        system = SystemChangeProposal(
            proposal_id="system-1", source_requirement_ref="requirement:database",
            proposed_scope="platform", required_behavior="Provide a managed database binding.",
            recurrence_count=2, affected_applications=("notes", "catalog"),
            evidence_refs=("requirement:database",), urgency="high", status="proposed",
        )
        decision = DistillationDecision(
            decision_id="decision-1", candidate_ref="capability:capability-1", decision="approve",
            reason="Evidence is sufficient.", decided_by="reviewer",
            evidence_refs=("bundle:bundle-1",),
        )
        report = DistillationReport(
            distillation_id="distillation-1", application_id="notes",
            evidence_bundle_ref="bundle:bundle-1", candidate_refs=(decision.candidate_ref,),
            decision_refs=("decision:decision-1",), proposal_refs=(blueprint.proposal_id, system.proposal_id),
            deterministic_metrics={"candidate_count": 1},
        )
        self.assertEqual(report.deterministic_metrics, {"candidate_count": 1})
        self.assertFalse(hasattr(blueprint, "source_patch"))


if __name__ == "__main__":
    unittest.main()
