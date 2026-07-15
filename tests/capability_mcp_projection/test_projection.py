from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_capability_mcp_projection",
    "servicefabric_capability_model",
    "servicefabric_capability_registry",
    "servicefabric_capability_runtime",
):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from servicefabric_capability_mcp_projection import (
    CapabilityMcpProjection,
    CapabilityMcpToolNotFoundError,
)
from servicefabric_capability_model import CapabilityDefinition
from servicefabric_capability_registry import CapabilityRegistry
from servicefabric_capability_runtime import (
    CapabilityAvailability,
    CapabilityAvailabilityReason,
    CapabilityAvailabilityState,
)


def declaration(identifier: str, title: str) -> CapabilityDefinition:
    return CapabilityDefinition.model_validate(
        {
            "apiVersion": "servicefabric.local/v1",
            "kind": "CapabilityDefinition",
            "metadata": {"id": identifier, "title": title, "domain": "notes"},
            "spec": {
                "operationRef": identifier,
                "objective": f"Perform {title.lower()}.",
                "capabilityClass": "retrieval",
                "concepts": ["notes"],
                "expectedInputs": ["request"],
                "expectedOutputs": ["result"],
                "effects": {
                    "effects": [
                        {
                            "effect_type": "external_read",
                            "target_category": "notes-store",
                            "scope": "application notes",
                            "reversibility": "not_applicable",
                            "verification_required": False,
                            "approval_required": False,
                            "idempotency_required": False,
                        }
                    ]
                },
            },
        }
    )


class CapabilityMcpProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.registry = CapabilityRegistry(Path(self.temporary.name) / "registry")
        self.registry.register(declaration("notes.search", "Search notes"), "research-notes")
        self.registry.register(declaration("notes.create", "Create note"), "research-notes")
        self.registry.register(declaration("admin.audit", "Audit notes"), "admin-console")
        self.runtime = Mock()
        self.runtime.availability.side_effect = self.availability
        self.projection = CapabilityMcpProjection(self.registry, self.runtime, "research-notes")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def availability(capability_id: str) -> CapabilityAvailability:
        available = capability_id == "notes.create"
        return CapabilityAvailability(
            capability_id,
            "research-notes",
            "notes-api",
            CapabilityAvailabilityState.AVAILABLE if available else CapabilityAvailabilityState.UNAVAILABLE,
            CapabilityAvailabilityReason.MODULE_HEALTHY if available else CapabilityAvailabilityReason.MODULE_STOPPED,
        )

    def test_lists_only_registered_application_capabilities_with_stable_names(self) -> None:
        candidates = self.projection.list_candidates()

        self.assertEqual([candidate.name for candidate in candidates], ["notes.create", "notes.search"])
        self.assertEqual([candidate.capability_id for candidate in candidates], ["notes.create", "notes.search"])
        self.assertEqual(candidates[0].title, "Create note")
        self.assertEqual(candidates[0].description, "Perform create note.")
        self.assertEqual(candidates[0].input_schema, {"type": "object", "additionalProperties": True})

    def test_candidates_retain_runtime_availability_without_hiding_registration(self) -> None:
        candidates = {candidate.capability_id: candidate for candidate in self.projection.list_candidates()}

        self.assertTrue(candidates["notes.create"].available)
        self.assertIsNone(candidates["notes.create"].unavailable_reason)
        self.assertFalse(candidates["notes.search"].available)
        self.assertEqual(candidates["notes.search"].unavailable_reason, "module_stopped")

    def test_calls_delegate_only_registered_names_to_capability_runtime(self) -> None:
        expected = {"capability_id": "notes.create", "output": {"id": 1}}
        self.runtime.invoke.return_value = expected

        result = self.projection.invoke("notes.create", {"title": "One"})

        self.assertEqual(result, expected)
        self.runtime.invoke.assert_called_once_with("notes.create", {"title": "One"})
        with self.assertRaises(CapabilityMcpToolNotFoundError):
            self.projection.invoke("admin.audit", {})
        self.runtime.invoke.assert_called_once()


if __name__ == "__main__":
    unittest.main()
