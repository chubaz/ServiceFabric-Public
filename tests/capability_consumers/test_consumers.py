from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "servicefabric_capability_consumers" / "src"))

from servicefabric_capability_consumers import (  # noqa: E402
    CapabilityClient,
    InternalAgentCapabilityAdapter,
    InternalAgentCapabilityReference,
)


class CapabilityConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = Mock()

    def test_client_delegates_discovery_availability_and_invocation_unchanged(self) -> None:
        availability = object()
        discovered = (object(), object())
        input_value = {"query": "capabilities"}
        result = {"capability_id": "notes.search", "output": ["one"]}
        self.runtime.availability.return_value = availability
        self.runtime.availability_for_application.return_value = discovered
        self.runtime.invoke.return_value = result
        client = CapabilityClient(self.runtime)

        self.assertIs(client.availability("notes.search"), availability)
        self.assertIs(client.discover("research-notes"), discovered)
        self.assertIs(client.invoke("notes.search", input_value), result)
        self.runtime.availability.assert_called_once_with("notes.search")
        self.runtime.availability_for_application.assert_called_once_with("research-notes")
        self.runtime.invoke.assert_called_once_with("notes.search", input_value)

    def test_internal_agent_reference_is_immutable(self) -> None:
        reference = InternalAgentCapabilityReference("notes.create")

        with self.assertRaises(FrozenInstanceError):
            reference.capability_id = "notes.search"  # type: ignore[misc]

    def test_agent_adapter_delegates_reference_without_business_logic(self) -> None:
        reference = InternalAgentCapabilityReference("notes.create")
        availability = object()
        input_value = {"title": "One", "body": "Body"}
        result = {"capability_id": "notes.create", "output": {"id": 1}}
        self.runtime.availability.return_value = availability
        self.runtime.invoke.return_value = result
        adapter = InternalAgentCapabilityAdapter(self.runtime)

        self.assertIs(adapter.availability(reference), availability)
        self.assertIs(adapter.invoke(reference, input_value), result)
        self.runtime.availability.assert_called_once_with("notes.create")
        self.runtime.invoke.assert_called_once_with("notes.create", input_value)


if __name__ == "__main__":
    unittest.main()
