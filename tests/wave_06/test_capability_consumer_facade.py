from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from servicefabric_client.capability_consumer import (
    CapabilityConsumerFacade,
    FrozenMapping,
)
from servicefabric_capability_runtime import (
    CapabilityAvailability,
    CapabilityAvailabilityReason,
    CapabilityAvailabilityState,
)


def _record(capability_id: str) -> object:
    return SimpleNamespace(
        definition=SimpleNamespace(
            metadata=SimpleNamespace(id=capability_id, title="Create note"),
            spec=SimpleNamespace(objective="Create a note", operation_ref="notes.create"),
        ),
        digest="sha256:example",
        application_ids=("research-notes",),
    )


class CapabilityConsumerFacadeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = Mock()
        self.runtime = Mock()
        self.facade = CapabilityConsumerFacade(self.registry, self.runtime)

    def test_list_and_describe_delegate_to_static_registry(self) -> None:
        self.registry.list.return_value = (_record("notes.create"),)
        self.registry.describe.return_value = _record("notes.create")

        listed = self.facade.list_capabilities("research-notes")
        described = self.facade.describe_capability("notes.create")

        self.registry.list.assert_called_once_with("research-notes")
        self.registry.describe.assert_called_once_with("notes.create")
        self.assertEqual(listed, (described,))
        self.assertEqual(described.application_ids, ("research-notes",))

    def test_availability_operations_delegate_to_runtime(self) -> None:
        availability = CapabilityAvailability(
            "notes.create",
            "research-notes",
            "api",
            CapabilityAvailabilityState.AVAILABLE,
            CapabilityAvailabilityReason.MODULE_HEALTHY,
        )
        self.runtime.availability.return_value = availability
        self.runtime.availability_for_application.return_value = (availability,)

        direct = self.facade.capability_availability("notes.create")
        listed = self.facade.availability_for_application("research-notes")

        self.runtime.availability.assert_called_once_with("notes.create")
        self.runtime.availability_for_application.assert_called_once_with("research-notes")
        self.assertTrue(direct.available)
        self.assertEqual(listed, (direct,))

    def test_invocation_delegates_without_revalidating_input(self) -> None:
        input_value = {"title": "One", "body": "Body"}
        self.runtime.invoke.return_value = {
            "capability_id": "notes.create",
            "operation_id": "notes.create",
            "binding_id": "api.notes.create",
            "output": {"id": 1, "tags": ["note"]},
        }

        invocation = self.facade.invoke_capability("notes.create", input_value)

        self.runtime.invoke.assert_called_once_with("notes.create", input_value)
        self.assertIsInstance(invocation.output, FrozenMapping)
        self.assertEqual(invocation.output["tags"], ("note",))


if __name__ == "__main__":
    unittest.main()
