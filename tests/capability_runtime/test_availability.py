from __future__ import annotations

import json
import unittest

from servicefabric_capability_runtime import (
    CapabilityAvailabilityReason,
    CapabilityAvailabilityResolver,
    CapabilityAvailabilityState,
    CapabilityRuntimeTarget,
    ModuleHealth,
    serialize_availability_snapshot,
)


class InMemoryModuleHealthSource:
    def __init__(self, records: dict[tuple[str, str], ModuleHealth]) -> None:
        self._records = records

    def get_module_health(self, application_id: str, module_id: str) -> ModuleHealth | None:
        return self._records.get((application_id, module_id))


class CapabilityAvailabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target = CapabilityRuntimeTarget("notes.create", "research-notes", "notes-api")

    def test_running_healthy_module_is_available(self) -> None:
        resolver = CapabilityAvailabilityResolver(
            InMemoryModuleHealthSource(
                {("research-notes", "notes-api"): ModuleHealth("research-notes", "notes-api", "running", "healthy")}
            )
        )

        result = resolver.resolve(self.target)

        self.assertEqual(result.state, CapabilityAvailabilityState.AVAILABLE)
        self.assertEqual(result.reason, CapabilityAvailabilityReason.MODULE_HEALTHY)
        self.assertTrue(result.available)

    def test_non_running_and_unhealthy_modules_are_unavailable_with_stable_reasons(self) -> None:
        cases = (
            (None, CapabilityAvailabilityReason.MODULE_NOT_FOUND),
            (ModuleHealth("research-notes", "notes-api", "starting", "unknown"), CapabilityAvailabilityReason.MODULE_STARTING),
            (ModuleHealth("research-notes", "notes-api", "stopped", "unavailable"), CapabilityAvailabilityReason.MODULE_STOPPED),
            (ModuleHealth("research-notes", "notes-api", "failed", "unhealthy"), CapabilityAvailabilityReason.MODULE_FAILED),
            (ModuleHealth("research-notes", "notes-api", "running", "unhealthy"), CapabilityAvailabilityReason.MODULE_UNHEALTHY),
        )
        for health, expected_reason in cases:
            with self.subTest(reason=expected_reason):
                records = {} if health is None else {("research-notes", "notes-api"): health}
                result = CapabilityAvailabilityResolver(InMemoryModuleHealthSource(records)).resolve(self.target)
                self.assertEqual(result.state, CapabilityAvailabilityState.UNAVAILABLE)
                self.assertEqual(result.reason, expected_reason)
                self.assertFalse(result.available)

    def test_snapshot_serialization_is_canonical_and_hides_runtime_details(self) -> None:
        resolver = CapabilityAvailabilityResolver(
            InMemoryModuleHealthSource(
                {("research-notes", "notes-api"): ModuleHealth("research-notes", "notes-api", "running", "healthy")}
            )
        )
        search = resolver.resolve(CapabilityRuntimeTarget("notes.search", "research-notes", "notes-api"))
        create = resolver.resolve(self.target)

        snapshot = serialize_availability_snapshot((search, create))

        self.assertEqual(snapshot, serialize_availability_snapshot((create, search)))
        self.assertEqual(
            json.loads(snapshot)["capabilities"],
            [create.to_dict(), search.to_dict()],
        )
        self.assertNotIn("endpoint", snapshot)


if __name__ == "__main__":
    unittest.main()
