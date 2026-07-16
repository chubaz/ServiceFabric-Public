from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_capability_mcp_projection",
):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))
sys.path.insert(0, str(ROOT / "clients" / "python"))

from servicefabric_client.capability_consumer import (
    CapabilityAvailability,
    CapabilityConsumerFacade,
    CapabilityDescription,
    CapabilityInvocation,
    FrozenMapping,
)
from servicefabric_capability_mcp_projection import CapabilityMcpProjection


class CapabilityMcpProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.consumer = Mock(spec=CapabilityConsumerFacade)
        self.consumer.list_capabilities.return_value = (
            CapabilityDescription(
                "notes.search",
                "Search notes",
                "Find a note.",
                "notes.search",
                "sha256:search",
                ("research-notes",),
            ),
            CapabilityDescription(
                "notes.create",
                "Create note",
                "Create a note.",
                "notes.create",
                "sha256:create",
                ("research-notes",),
            ),
        )
        self.consumer.availability_for_application.return_value = (
            CapabilityAvailability(
                "notes.search",
                "research-notes",
                "notes-api",
                "unavailable",
                "module_stopped",
            ),
            CapabilityAvailability(
                "notes.create",
                "research-notes",
                "notes-api",
                "available",
                "module_healthy",
            ),
        )
        self.projection = CapabilityMcpProjection(self.consumer, "research-notes")

    def test_lists_only_registered_application_capabilities_with_stable_names(self) -> None:
        candidates = self.projection.list_candidates()

        self.assertEqual([candidate.name for candidate in candidates], ["notes.create", "notes.search"])
        self.assertEqual([candidate.capability_id for candidate in candidates], ["notes.create", "notes.search"])
        self.assertEqual(candidates[0].title, "Create note")
        self.assertEqual(candidates[0].description, "Create a note.")
        self.assertEqual(candidates[0].input_schema, {"type": "object", "additionalProperties": True})
        self.consumer.list_capabilities.assert_called_once_with("research-notes")
        self.consumer.availability_for_application.assert_called_once_with("research-notes")

    def test_candidates_retain_runtime_availability_without_hiding_registration(self) -> None:
        candidates = {candidate.capability_id: candidate for candidate in self.projection.list_candidates()}

        self.assertTrue(candidates["notes.create"].available)
        self.assertIsNone(candidates["notes.create"].unavailable_reason)
        self.assertFalse(candidates["notes.search"].available)
        self.assertEqual(candidates["notes.search"].unavailable_reason, "module_stopped")

    def test_calls_delegate_unchanged_to_capability_consumer_facade(self) -> None:
        expected = CapabilityInvocation(
            "notes.create",
            "notes.create",
            "api.notes.create",
            FrozenMapping((("id", 1),)),
        )
        arguments = {"title": "One"}
        self.consumer.invoke_capability.return_value = expected

        result = self.projection.invoke("notes.create", arguments)

        self.assertEqual(result, expected)
        self.consumer.invoke_capability.assert_called_once_with("notes.create", arguments)
        self.assertIs(self.consumer.invoke_capability.call_args.args[1], arguments)
        self.consumer.list_capabilities.assert_not_called()
        self.consumer.availability_for_application.assert_not_called()


if __name__ == "__main__":
    unittest.main()
