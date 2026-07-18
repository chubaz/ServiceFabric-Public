from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from servicefabric_distillation_contracts import DistillationDecision, EngineeringPatternCandidate
from servicefabric_engineering_distillation import (
    EngineeringPatternCatalog,
    EngineeringPatternCatalogError,
    EngineeringPatternConflictError,
    EngineeringPatternNotFoundError,
    EngineeringPatternStorageError,
    engineering_pattern_content_digest,
)


def candidate(identifier: str = "factory.parallel_lanes", status: str = "proposed") -> EngineeringPatternCandidate:
    return EngineeringPatternCandidate(
        candidate_id=identifier,
        source_blueprint_ref="blueprints/factory@1.0.0",
        lane_topology=("analysis", "publication"),
        provider_role_mapping={"analysis": "provider.analysis"},
        path_ownership={"analysis": ("packages/analysis",)},
        dependency_order=("analysis", "publication"),
        verification_profile=("python3 -m unittest",),
        observed_usage_ref="applications/example@abc1234",
        evidence_refs=("evidence/factory-run",),
        status=status,
    )


def approval(candidate_id: str = "factory.parallel_lanes", decision: str = "approve") -> DistillationDecision:
    return DistillationDecision(
        decision_id="review.factory.parallel_lanes",
        candidate_ref=candidate_id,
        decision=decision,
        reason="Reviewed reusable pattern.",
        decided_by="reviewer@example.test",
        evidence_refs=("evidence/factory-run",),
    )


class EngineeringPatternCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "catalog"
        self.catalog = EngineeringPatternCatalog(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_publishes_describes_and_hashes_an_approved_exact_version(self) -> None:
        pattern = candidate()
        result = self.catalog.publish(pattern, approval(), "1.0.0")
        described = self.catalog.describe(pattern.candidate_id, "1.0.0")
        self.assertTrue(result.created)
        self.assertEqual(described.candidate, pattern)
        self.assertEqual(described.digest, engineering_pattern_content_digest(pattern))
        self.assertEqual(described.decision.decision, "approve")

    def test_identical_publication_is_idempotent(self) -> None:
        first = self.catalog.publish(candidate(), approval(), "1.0.0")
        second = self.catalog.publish(candidate(), approval(), "1.0.0")
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(self.catalog.list(), (second.publication,))

    def test_rejects_conflicting_exact_version_without_mutation(self) -> None:
        self.catalog.publish(candidate(), approval(), "1.0.0")
        changed = candidate(status="revised")
        with self.assertRaises(EngineeringPatternConflictError):
            self.catalog.publish(changed, approval(), "1.0.0")
        self.assertEqual(self.catalog.describe("factory.parallel_lanes", "1.0.0").candidate, candidate())

    def test_rejects_unapproved_or_mismatched_decisions(self) -> None:
        with self.assertRaises(EngineeringPatternCatalogError):
            self.catalog.publish(candidate(), approval(decision="reject"), "1.0.0")
        with self.assertRaises(EngineeringPatternCatalogError):
            self.catalog.publish(candidate(), approval("factory.other"), "1.0.0")
        self.assertFalse(self.root.exists())

    def test_lists_in_deterministic_pattern_and_version_order(self) -> None:
        beta = candidate("factory.beta")
        alpha = candidate("factory.alpha")
        self.catalog.publish(beta, approval("factory.beta"), "2.0.0")
        self.catalog.publish(alpha, approval("factory.alpha"), "2.0.0")
        self.catalog.publish(alpha, approval("factory.alpha"), "1.0.0")
        self.assertEqual(
            [(item.pattern_id, item.version) for item in self.catalog.list()],
            [("factory.alpha", "1.0.0"), ("factory.alpha", "2.0.0"), ("factory.beta", "2.0.0")],
        )
        self.assertEqual([item.version for item in self.catalog.list("factory.alpha")], ["1.0.0", "2.0.0"])

    def test_rejects_unknown_versions_and_unsafe_storage_paths(self) -> None:
        with self.assertRaises(EngineeringPatternNotFoundError):
            self.catalog.describe("factory.missing", "1.0.0")
        with self.assertRaises(EngineeringPatternStorageError):
            self.catalog.publish(candidate(), approval(), "../outside")
        self.assertEqual(self.catalog.list(), ())

    def test_rejects_symlinked_root_state_and_lock(self) -> None:
        target = Path(self.temporary.name) / "target"
        target.mkdir()
        self.root.symlink_to(target, target_is_directory=True)
        with self.assertRaises(EngineeringPatternStorageError):
            self.catalog.list()
        self.root.unlink()
        self.catalog.publish(candidate(), approval(), "1.0.0")
        state = self.root / "engineering-pattern-catalog.json"
        replacement = self.root / "replacement.json"
        replacement.write_text(json.dumps({"version": 1, "patterns": {}}), encoding="utf-8")
        state.unlink()
        state.symlink_to(replacement)
        with self.assertRaises(EngineeringPatternStorageError):
            self.catalog.list()
        state.unlink()
        self.root.joinpath(".engineering-pattern-catalog.lock").unlink()
        self.root.joinpath(".engineering-pattern-catalog.lock").symlink_to(replacement)
        with self.assertRaises(EngineeringPatternStorageError):
            self.catalog.publish(candidate(), approval(), "2.0.0")

    def test_rejects_malformed_persisted_publications(self) -> None:
        self.root.mkdir()
        self.root.joinpath("engineering-pattern-catalog.json").write_text(
            json.dumps({"version": 1, "patterns": {"factory.parallel_lanes": {"1.0.0": {}}}}),
            encoding="utf-8",
        )
        with self.assertRaises(EngineeringPatternStorageError):
            self.catalog.list()

    def test_atomic_write_failure_preserves_previous_catalog(self) -> None:
        self.catalog.publish(candidate(), approval(), "1.0.0")
        before = self.root.joinpath("engineering-pattern-catalog.json").read_bytes()
        with mock.patch("servicefabric_engineering_distillation.catalog.os.replace", side_effect=OSError("disk failure")):
            with self.assertRaises(EngineeringPatternStorageError):
                self.catalog.publish(candidate("factory.second"), approval("factory.second"), "1.0.0")
        self.assertEqual(self.root.joinpath("engineering-pattern-catalog.json").read_bytes(), before)
        self.assertFalse(list(self.root.glob(".engineering-pattern-catalog-*.tmp")))


if __name__ == "__main__":
    unittest.main()
