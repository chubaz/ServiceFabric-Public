"""Project registered capabilities without owning their invocation behavior."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

class RuntimeAvailability(Protocol):
    """The bounded availability fields exposed by the capability runtime."""

    capability_id: str
    application_id: str
    available: bool
    reason: object


class CapabilityRuntime(Protocol):
    """The Wave-5 runtime surface consumed by the MCP projection."""

    def availability_for_application(self, application_id: str) -> tuple[RuntimeAvailability, ...]:
        """Discover registered capabilities with their current availability."""

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


class CapabilityMcpProjection:
    """Expose one application's registered capabilities as MCP candidates.

    The projection derives discovery data only. Calls are delegated to the
    supplied ``CapabilityRuntimeService`` and never resolve an application
    endpoint or duplicate canonical validation here.
    """

    def __init__(
        self,
        runtime: CapabilityRuntime,
        application_id: str,
    ) -> None:
        self._runtime = runtime
        self._application_id = application_id

    def list_candidates(self) -> tuple[CapabilityMcpCandidate, ...]:
        """Return stable, availability-aware candidates in capability-ID order."""

        candidates = []
        for availability in self._runtime.availability_for_application(self._application_id):
            capability_id = availability.capability_id
            reason = None if availability.available else _reason_value(availability.reason)
            candidates.append(
                CapabilityMcpCandidate(
                    name=capability_id,
                    capability_id=capability_id,
                    application_id=self._application_id,
                    title=capability_id,
                    description=f"Registered ServiceFabric capability {capability_id}.",
                    input_schema={"type": "object", "additionalProperties": True},
                    available=availability.available,
                    unavailable_reason=reason,
                )
            )
        return tuple(sorted(candidates, key=lambda candidate: candidate.capability_id))

    def invoke(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Delegate an MCP call unchanged to the canonical runtime."""

        return self._runtime.invoke(name, arguments)


def _reason_value(reason: object) -> str:
    value = getattr(reason, "value", reason)
    return str(value)
