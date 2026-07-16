"""Business-logic-free consumers of ``CapabilityRuntimeService``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias


class _CapabilityRuntimeService(Protocol):
    """The public Wave-5 runtime surface consumed by projections."""

    def availability(self, capability_id: str) -> Any:
        """Return live availability for one registered capability."""

    def availability_for_application(self, application_id: str) -> tuple[Any, ...]:
        """Return registered capability availability for one application."""

    def invoke(self, capability_id: str, input_value: Any) -> dict[str, Any]:
        """Invoke one registered capability through the canonical runtime."""


class CapabilityClient:
    """Generic in-process SDK facade over ``CapabilityRuntimeService``."""

    def __init__(self, runtime: _CapabilityRuntimeService) -> None:
        self._runtime = runtime

    def availability(self, capability_id: str) -> Any:
        """Return runtime availability without interpreting it."""

        return self._runtime.availability(capability_id)

    def discover(self, application_id: str) -> tuple[Any, ...]:
        """Discover registered capabilities through the runtime service."""

        return self._runtime.availability_for_application(application_id)

    def invoke(self, capability_id: str, input_value: Any) -> dict[str, Any]:
        """Invoke through the runtime service without adapting the payload."""

        return self._runtime.invoke(capability_id, input_value)


@dataclass(frozen=True, slots=True)
class InternalAgentCapabilityReference:
    """Immutable internal-agent reference to a registered capability."""

    capability_id: str


class InternalAgentCapabilityAdapter:
    """Resolve internal-agent references only through the capability runtime."""

    def __init__(self, runtime: _CapabilityRuntimeService) -> None:
        self._runtime = runtime

    def availability(self, reference: InternalAgentCapabilityReference) -> Any:
        """Return live availability for the referenced capability."""

        return self._runtime.availability(reference.capability_id)

    def invoke(self, reference: InternalAgentCapabilityReference, input_value: Any) -> dict[str, Any]:
        """Invoke the referenced capability without adding agent business logic."""

        return self._runtime.invoke(reference.capability_id, input_value)


AgentCapabilityReference: TypeAlias = InternalAgentCapabilityReference
AgentCapabilityAdapter: TypeAlias = InternalAgentCapabilityAdapter
