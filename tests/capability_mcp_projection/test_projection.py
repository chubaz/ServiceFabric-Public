from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_capability_mcp_projection",
    "servicefabric_capability_runtime",
):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from servicefabric_capability_mcp_projection import (
    CapabilityMcpProjection,
)
from servicefabric_capability_runtime import (
    CapabilityAvailability,
    CapabilityAvailabilityReason,
    CapabilityAvailabilityState,
)


class CapabilityMcpProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = Mock()
        self.runtime.availability_for_application.return_value = (
            CapabilityAvailability(
                "notes.search",
                "research-notes",
                "notes-api",
                CapabilityAvailabilityState.UNAVAILABLE,
                CapabilityAvailabilityReason.MODULE_STOPPED,
            ),
            CapabilityAvailability(
                "notes.create",
                "research-notes",
                "notes-api",
                CapabilityAvailabilityState.AVAILABLE,
                CapabilityAvailabilityReason.MODULE_HEALTHY,
            ),
        )
        self.projection = CapabilityMcpProjection(self.runtime, "research-notes")

    def test_lists_only_registered_application_capabilities_with_stable_names(self) -> None:
        candidates = self.projection.list_candidates()

        self.assertEqual([candidate.name for candidate in candidates], ["notes.create", "notes.search"])
        self.assertEqual([candidate.capability_id for candidate in candidates], ["notes.create", "notes.search"])
        self.assertEqual(candidates[0].title, "notes.create")
        self.assertEqual(candidates[0].description, "Registered ServiceFabric capability notes.create.")
        self.assertEqual(candidates[0].input_schema, {"type": "object", "additionalProperties": True})
        self.runtime.availability_for_application.assert_called_once_with("research-notes")

    def test_candidates_retain_runtime_availability_without_hiding_registration(self) -> None:
        candidates = {candidate.capability_id: candidate for candidate in self.projection.list_candidates()}

        self.assertTrue(candidates["notes.create"].available)
        self.assertIsNone(candidates["notes.create"].unavailable_reason)
        self.assertFalse(candidates["notes.search"].available)
        self.assertEqual(candidates["notes.search"].unavailable_reason, "module_stopped")

    def test_calls_delegate_unchanged_to_capability_runtime(self) -> None:
        expected = {"capability_id": "notes.create", "output": {"id": 1}}
        arguments = {"title": "One"}
        self.runtime.invoke.return_value = expected

        result = self.projection.invoke("notes.create", arguments)

        self.assertEqual(result, expected)
        self.runtime.invoke.assert_called_once_with("notes.create", arguments)
        self.assertIs(self.runtime.invoke.call_args.args[1], arguments)
        self.runtime.availability_for_application.assert_not_called()


if __name__ == "__main__":
    unittest.main()
