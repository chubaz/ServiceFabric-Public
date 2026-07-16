"""Integration-owned composition for capability consumer projections."""

from __future__ import annotations

from dataclasses import dataclass

from servicefabric_capability_consumers import (
    CapabilityClient,
    InternalAgentCapabilityAdapter,
)
from servicefabric_capability_mcp_projection import CapabilityMcpProjection
from servicefabric_capability_rest_gateway import CapabilityRestGateway
from servicefabric_workspace import WorkspaceLayout

from .capability_consumer import CapabilityConsumerFacade


class _FacadeRuntimeAdapter:
    """Present the accepted runtime-shaped SDK boundary over one facade."""

    def __init__(self, facade: CapabilityConsumerFacade) -> None:
        self.facade = facade

    def availability(self, capability_id: str) -> object:
        return self.facade.capability_availability(capability_id)

    def availability_for_application(self, application_id: str) -> tuple[object, ...]:
        return self.facade.availability_for_application(application_id)

    def invoke(self, capability_id: str, input_value: object) -> object:
        return self.facade.invoke_capability(capability_id, input_value)


@dataclass(frozen=True, slots=True)
class CapabilityProjectionComposition:
    """All accepted capability projections sharing one facade instance."""

    facade: CapabilityConsumerFacade
    rest_gateway: CapabilityRestGateway
    capability_client: CapabilityClient
    agent_adapter: InternalAgentCapabilityAdapter
    _runtime_adapter: _FacadeRuntimeAdapter

    @classmethod
    def for_workspace(cls, workspace: WorkspaceLayout) -> "CapabilityProjectionComposition":
        return cls.from_facade(CapabilityConsumerFacade.for_workspace(workspace))

    @classmethod
    def from_facade(cls, facade: CapabilityConsumerFacade) -> "CapabilityProjectionComposition":
        runtime_adapter = _FacadeRuntimeAdapter(facade)
        return cls(
            facade=facade,
            rest_gateway=CapabilityRestGateway(facade),
            capability_client=CapabilityClient(runtime_adapter),
            agent_adapter=InternalAgentCapabilityAdapter(runtime_adapter),
            _runtime_adapter=runtime_adapter,
        )

    def mcp_projection(self, application_id: str) -> CapabilityMcpProjection:
        """Create an application-scoped MCP view over the shared facade."""

        return CapabilityMcpProjection(self.facade, application_id)
