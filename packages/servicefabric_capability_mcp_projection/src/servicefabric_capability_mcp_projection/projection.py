"""Project registered capabilities without owning their invocation behavior."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from servicefabric_capability_registry import CapabilityRecord


class CapabilityRegistryView(Protocol):
    """The static registry operation consumed by the projection."""

    def list_capabilities(self, application_id: str | None = None) -> tuple[CapabilityRecord, ...]:
        """Return explicitly registered capabilities for an application."""


class RuntimeAvailability(Protocol):
    """The bounded availability fields exposed by the capability runtime."""

    capability_id: str
    available: bool
    reason: object


class CapabilityRuntime(Protocol):
    """The Wave-5 runtime surface consumed by the MCP projection."""

    def availability(self, capability_id: str) -> RuntimeAvailability:
        """Return current availability for a registered capability."""

    def invoke(self, capability_id: str, input_value: Any) -> dict[str, Any]:
        """Invoke through the canonical capability runtime."""


@dataclass(frozen=True, slots=True)
class CapabilityMcpCandidate:
    """An MCP-facing view that retains the canonical capability identity."""

    name: str
    capability_id: str
    application_id: str
    title: str
    description: str
    input_schema: dict[str, object]
    available: bool
    unavailable_reason: str | None


class CapabilityMcpToolNotFoundError(LookupError):
    """Raised when an MCP name is not registered for the projected application."""


class CapabilityMcpProjection:
    """Expose one application's registered capabilities as MCP candidates.

    The projection derives discovery data only. Calls are delegated to the
    supplied ``CapabilityRuntimeService`` and never resolve an application
    endpoint or duplicate canonical validation here.
    """

    def __init__(
        self,
        registry: CapabilityRegistryView,
        runtime: CapabilityRuntime,
        application_id: str,
    ) -> None:
        self._registry = registry
        self._runtime = runtime
        self._application_id = application_id

    def list_candidates(self) -> tuple[CapabilityMcpCandidate, ...]:
        """Return stable, availability-aware candidates in capability-ID order."""

        candidates = []
        for record in self._registry.list_capabilities(self._application_id):
            definition = record.definition
            capability_id = definition.metadata.id
            availability = self._runtime.availability(capability_id)
            reason = None if availability.available else _reason_value(availability.reason)
            candidates.append(
                CapabilityMcpCandidate(
                    name=capability_id,
                    capability_id=capability_id,
                    application_id=self._application_id,
                    title=definition.metadata.title,
                    description=definition.spec.objective,
                    input_schema={"type": "object", "additionalProperties": True},
                    available=availability.available,
                    unavailable_reason=reason,
                )
            )
        return tuple(sorted(candidates, key=lambda candidate: candidate.capability_id))

    def invoke(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Delegate an explicitly projected MCP call to the canonical runtime."""

        capability_ids = {
            record.definition.metadata.id
            for record in self._registry.list_capabilities(self._application_id)
        }
        if name not in capability_ids:
            raise CapabilityMcpToolNotFoundError(
                f"MCP capability '{name}' is not registered for application '{self._application_id}'"
            )
        return self._runtime.invoke(name, dict(arguments))


def _reason_value(reason: object) -> str:
    value = getattr(reason, "value", reason)
    return str(value)
