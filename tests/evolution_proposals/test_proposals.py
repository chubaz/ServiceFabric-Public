"""Focused behavior tests for evidence-backed evolution proposal records."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "packages/servicefabric_evolution_proposals/src"),
    str(ROOT / "packages/servicefabric_distillation_contracts/src"),
    str(ROOT / "packages/servicefabric_capability_model/src"),
    str(ROOT / "packages/servicefabric_contracts/src"),
]

from servicefabric_distillation_contracts import ApplicationEvidenceBundle
from servicefabric_evolution_proposals import (
    EvolutionProposalError,
    propose_blueprint_evolutions,
    propose_system_changes,
)


def _bundle(bundle_id: str, application_id: str, *requirements: str) -> ApplicationEvidenceBundle:
    return ApplicationEvidenceBundle(
        bundle_id=bundle_id,
        application_id=application_id,
        repository_head="a" * 40,
        application_blueprint_id="payments-blueprint",
        exact_manifest_refs=("manifest:payments-v1",),
        verification_evidence_refs=("verification:payments",),
        unmet_requirement_refs=requirements,
    )


class EvolutionProposalTests(unittest.TestCase):
    def test_blueprint_proposals_are_deterministic_evidence_backed_records(self) -> None:
        bundle = _bundle("bundle-a", "payments", "requirement:z", "requirement:a")

        proposals = propose_blueprint_evolutions(
            bundle,
            blueprint_version="1.2.0",
            category_by_requirement={"requirement:a": "verification"},
        )

        self.assertEqual([proposal.category for proposal in proposals], ["verification", "guidance"])
        self.assertEqual(
            proposals[0].evidence_refs,
            ("manifest:payments-v1", "requirement:a", "verification:payments"),
        )
        self.assertEqual(proposals[0].status, "proposed")
        self.assertIn("does not modify the blueprint", proposals[0].proposed_change)

    def test_system_proposals_require_recurrence_and_explicit_scope(self) -> None:
        bundles = (
            _bundle("bundle-a", "payments", "requirement:observability"),
            _bundle("bundle-b", "orders", "requirement:observability"),
            _bundle("bundle-c", "catalog", "requirement:other"),
        )

        proposals = propose_system_changes(
            bundles,
            scope_by_requirement={"requirement:observability": "platform"},
        )

        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal.recurrence_count, 2)
        self.assertEqual(proposal.affected_applications, ("orders", "payments"))
        self.assertEqual(proposal.proposed_scope, "platform")
        self.assertEqual(proposal.status, "proposed")

    def test_system_proposals_do_not_infer_scope(self) -> None:
        bundles = (_bundle("bundle-a", "payments", "requirement:shared"),) * 2

        with self.assertRaisesRegex(EvolutionProposalError, "explicit scope"):
            propose_system_changes(bundles, scope_by_requirement={}, minimum_recurrence=2)


if __name__ == "__main__":
    unittest.main()
