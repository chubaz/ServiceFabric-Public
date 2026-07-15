from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from servicefabric_capability_model import CapabilityDefinition
from servicefabric_capability_registry import (
    CapabilityConflictError,
    CapabilityNotFoundError,
    CapabilityRegistry,
    CapabilityStorageError,
    capability_content_digest,
)


def declaration(identifier: str = "research.scholarship_search", objective: str = "Discover scholarly records.") -> CapabilityDefinition:
    return CapabilityDefinition.model_validate({
        "apiVersion": "servicefabric.local/v1",
        "kind": "CapabilityDefinition",
        "metadata": {"id": identifier, "title": "Scholarly Search", "domain": "research"},
        "spec": {
            "operationRef": "research.search_papers",
            "objective": objective,
            "capabilityClass": "retrieval",
            "concepts": ["papers"],
            "expectedInputs": ["query"],
            "expectedOutputs": ["records"],
            "effects": {"effects": [{
                "effect_type": "external_read",
                "target_category": "scholarly-service",
                "scope": "public records",
                "reversibility": "not_applicable",
                "verification_required": False,
                "approval_required": False,
                "idempotency_required": False,
            }]},
        },
    })


class CapabilityRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "registry"
        self.registry = CapabilityRegistry(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_register_describe_and_content_digest(self) -> None:
        capability = declaration()
        result = self.registry.register(capability, "research-notes")
        described = self.registry.describe(capability.metadata.id)
        self.assertTrue(result.created)
        self.assertTrue(result.application_link_created)
        self.assertEqual(described.definition, capability)
        self.assertEqual(described.digest, capability_content_digest(capability))
        self.assertEqual(described.application_ids, ("research-notes",))

    def test_identical_registration_is_idempotent(self) -> None:
        capability = declaration()
        first = self.registry.register(capability, "research-notes")
        second = self.registry.register(capability, "research-notes")
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertFalse(second.application_link_created)
        self.assertEqual(self.registry.list(), (second.record,))

    def test_rejects_same_identifier_with_different_static_content_without_mutation(self) -> None:
        first = declaration()
        self.registry.register(first, "research-notes")
        with self.assertRaises(CapabilityConflictError):
            self.registry.register(declaration(objective="Discover peer-reviewed records."), "research-notes")
        self.assertEqual(self.registry.describe(first.metadata.id).definition, first)

    def test_lists_deterministically_and_uses_application_index(self) -> None:
        beta = declaration("research.beta")
        alpha = declaration("research.alpha")
        self.registry.register(beta, "app-b")
        self.registry.register(alpha, "app-a")
        self.registry.register(alpha, "app-b")
        self.assertEqual([record.definition.metadata.id for record in self.registry.list()], ["research.alpha", "research.beta"])
        self.assertEqual([record.definition.metadata.id for record in self.registry.list("app-a")], ["research.alpha"])
        self.assertEqual([record.definition.metadata.id for record in self.registry.list("app-b")], ["research.alpha", "research.beta"])

    def test_unknown_capability_is_rejected(self) -> None:
        with self.assertRaises(CapabilityNotFoundError):
            self.registry.describe("research.missing")

    def test_rejects_path_traversal_application_identifier(self) -> None:
        with self.assertRaises(CapabilityStorageError):
            self.registry.register(declaration(), "../outside")
        self.assertFalse(self.root.exists())

    def test_rejects_symlink_root_and_state_file(self) -> None:
        target = Path(self.temporary.name) / "target"
        target.mkdir()
        self.root.symlink_to(target, target_is_directory=True)
        with self.assertRaises(CapabilityStorageError):
            self.registry.list()
        self.root.unlink()
        self.registry.register(declaration(), "research-notes")
        state = self.root / "capability-registry.json"
        replacement = self.root / "replacement.json"
        replacement.write_text(json.dumps({"version": 1, "capabilities": {}, "applications": {}}), encoding="utf-8")
        state.unlink()
        state.symlink_to(replacement)
        with self.assertRaises(CapabilityStorageError):
            self.registry.list()

    def test_state_is_atomically_replaced_static_json(self) -> None:
        self.registry.register(declaration(), "research-notes")
        state = json.loads((self.root / "capability-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(set(state), {"version", "capabilities", "applications"})
        self.assertEqual(state["applications"], {"research-notes": ["research.scholarship_search"]})


if __name__ == "__main__":
    unittest.main()
