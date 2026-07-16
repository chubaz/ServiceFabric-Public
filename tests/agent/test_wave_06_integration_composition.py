from __future__ import annotations

import unittest
from pathlib import Path
import sys
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]
for source in (
    ROOT / "packages" / "servicefabric_capability_consumers" / "src",
    ROOT / "packages" / "servicefabric_capability_mcp_projection" / "src",
    ROOT / "services" / "capability_rest_gateway" / "src",
    ROOT / "clients" / "python",
):
    sys.path.insert(0, str(source))

from servicefabric_capability_consumers import InternalAgentCapabilityReference
from servicefabric_client.capability_consumer import (
    CapabilityAvailability,
    CapabilityConsumerFacade,
    CapabilityDescription,
    CapabilityInvocation,
)
from servicefabric_client.capability_projections import CapabilityProjectionComposition


class Wave06IntegrationCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.facade = Mock(spec=CapabilityConsumerFacade)
        self.composition = CapabilityProjectionComposition.from_facade(self.facade)

    def test_mcp_delegates_through_shared_consumer_facade(self) -> None:
        description = CapabilityDescription(
            "notes.create",
            "Create note",
            "Create a note.",
            "notes.create",
            "sha256:create",
            ("research-notes",),
        )
        availability = CapabilityAvailability(
            "notes.create", "research-notes", "notes-api", "available", "module_healthy"
        )
        invocation = CapabilityInvocation(
            "notes.create", "notes.create", "api.notes.create", 1
        )
        self.facade.list_capabilities.return_value = (description,)
        self.facade.availability_for_application.return_value = (availability,)
        self.facade.invoke_capability.return_value = invocation

        projection = self.composition.mcp_projection("research-notes")
        listed = projection.list_candidates()
        result = projection.invoke("notes.create", {"title": "One"})

        self.assertIs(projection._consumer, self.composition.facade)
        self.assertEqual([candidate.name for candidate in listed], ["notes.create"])
        self.assertIs(result, invocation)
        self.facade.invoke_capability.assert_called_once_with("notes.create", {"title": "One"})

    def test_rest_delegates_through_same_consumer_facade(self) -> None:
        invocation = CapabilityInvocation(
            "notes.create", "notes.create", "api.notes.create", 1
        )
        self.facade.invoke_capability.return_value = invocation

        result = self.composition.rest_gateway.invoke("notes.create", {"title": "One"})

        self.assertIs(self.composition.rest_gateway._consumer, self.composition.facade)
        self.assertEqual(result["capabilityId"], "notes.create")
        self.facade.invoke_capability.assert_called_once_with("notes.create", {"title": "One"})

    def test_python_and_agent_exports_delegate_through_same_facade(self) -> None:
        availability = CapabilityAvailability(
            "notes.create", "research-notes", "notes-api", "available", "module_healthy"
        )
        invocation = CapabilityInvocation(
            "notes.create", "notes.create", "api.notes.create", 1
        )
        self.facade.capability_availability.return_value = availability
        self.facade.invoke_capability.return_value = invocation
        reference = InternalAgentCapabilityReference("notes.create")

        client_availability = self.composition.capability_client.availability("notes.create")
        agent_result = self.composition.agent_adapter.invoke(reference, {"title": "One"})

        self.assertIs(self.composition._runtime_adapter.facade, self.composition.facade)
        self.assertIs(client_availability, availability)
        self.assertIs(agent_result, invocation)
        self.facade.capability_availability.assert_called_once_with("notes.create")
        self.facade.invoke_capability.assert_called_once_with("notes.create", {"title": "One"})


if __name__ == "__main__":
    unittest.main()
