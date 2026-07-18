from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_contracts",
    "servicefabric_capability_model",
    "servicefabric_distillation_contracts",
    "servicefabric_operation_model",
    "servicefabric_capability_distillation",
):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))
sys.path.insert(0, str(ROOT / "packages" / "servicefabric_operation_model"))

from servicefabric_capability_distillation import (  # noqa: E402
    CapabilityDistillationError,
    CapabilityDistillationRequest,
    distill_capability_candidates,
)
from servicefabric_capability_model import (  # noqa: E402
    CapabilityDefinition,
    CapabilityDefinitionSpec,
    CapabilityMetadata,
)
from servicefabric_contracts.effects import EffectContract, EffectDeclaration  # noqa: E402
from servicefabric_distillation_contracts import ApplicationEvidenceBundle  # noqa: E402
from servicefabric_operation_model import HttpBinding, OperationDefinition  # noqa: E402


def _operation(identifier: str = "notes.search") -> OperationDefinition:
    return OperationDefinition(
        operation_id=identifier,
        version="1.0.0",
        application_ref="notes",
        module_ref="notes-api",
        interface_ref="notes-api",
        bindings=(HttpBinding("notes-search", "GET", "/notes"),),
    )


def _capability(identifier: str = "notes.search", operation_ref: str = "notes.search") -> CapabilityDefinition:
    return CapabilityDefinition(
        api_version="servicefabric.local/v1",
        kind="CapabilityDefinition",
        metadata=CapabilityMetadata(id=identifier, title="Search notes", domain="notes"),
        spec=CapabilityDefinitionSpec(
            operation_ref=operation_ref,
            objective="Search explicitly declared notes.",
            capability_class="retrieval",
            concepts=("notes",), expected_inputs=("query",), expected_outputs=("matches",),
            effect_contract=EffectContract(effects=(EffectDeclaration(
                effect_type="external_read", target_category="notes", scope="notes",
                reversibility="not_applicable", verification_required=False,
                approval_required=False, idempotency_required=False,
            ),)),
        ),
    )


def _bundle(**changes: object) -> ApplicationEvidenceBundle:
    values: dict[str, object] = {
        "bundle_id": "notes-run-1", "application_id": "notes", "repository_head": "abcdef0",
        "application_blueprint_id": "notes-blueprint", "operation_refs": ("notes.search",),
        "capability_refs": ("notes.search",),
        "exact_manifest_refs": ("manifest:notes",),
        "verification_evidence_refs": ("verification:notes",),
    }
    values.update(changes)
    return ApplicationEvidenceBundle(**values)


class CapabilityDistillationTests(unittest.TestCase):
    def test_creates_deterministic_proposed_candidate_without_publication(self) -> None:
        request = CapabilityDistillationRequest(
            _bundle(), (_operation(),), (_capability(),), ("verification:notes",),
        )
        candidate, = distill_capability_candidates(request)
        self.assertEqual(candidate.candidate_id, "capability-candidate.notes-run-1.notes.search")
        self.assertEqual(candidate.evidence_refs, ("bundle:notes-run-1", "verification:notes"))
        self.assertEqual(candidate.status, "proposed")
        self.assertEqual(candidate.proposed_definition, _capability())

    def test_rejects_operations_not_named_by_evidence_bundle(self) -> None:
        with self.assertRaisesRegex(CapabilityDistillationError, "not named by evidence bundle"):
            distill_capability_candidates(CapabilityDistillationRequest(
                _bundle(operation_refs=()), (_operation(),), (_capability(),),
            ))

    def test_rejects_capabilities_or_evidence_outside_the_bundle(self) -> None:
        with self.assertRaisesRegex(CapabilityDistillationError, "capability .*not named"):
            distill_capability_candidates(CapabilityDistillationRequest(
                _bundle(capability_refs=("notes.other",)), (_operation(),), (_capability(),),
            ))
        with self.assertRaisesRegex(CapabilityDistillationError, "not named by bundle"):
            distill_capability_candidates(CapabilityDistillationRequest(
                _bundle(), (_operation(),), (_capability(),), ("file:unbounded",),
            ))

    def test_never_uses_routes_to_discover_undeclared_operations(self) -> None:
        with self.assertRaisesRegex(CapabilityDistillationError, "undeclared operation"):
            distill_capability_candidates(CapabilityDistillationRequest(
                _bundle(), (_operation(),), (_capability(operation_ref="notes.unknown"),),
            ))


if __name__ == "__main__":
    unittest.main()
