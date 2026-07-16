"""Project registered capabilities without owning their invocation behavior."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from servicefabric_client.capability_consumer import (
    CapabilityAvailability,
    CapabilityConsumerFacade,
    CapabilityInvocation,
)


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
    integration-owned capability consumer facade and never resolve an
    application endpoint or duplicate canonical validation here.
    """

    def __init__(
        self,
        consumer: CapabilityConsumerFacade,
        application_id: str,
    ) -> None:
        self._consumer = consumer
        self._application_id = application_id

    def list_candidates(self) -> tuple[CapabilityMcpCandidate, ...]:
        """Return stable, availability-aware candidates in capability-ID order."""

        availability_by_id = {
            availability.capability_id: availability
            for availability in self._consumer.availability_for_application(self._application_id)
        }
        candidates_by_id = {}
        for description in self._consumer.list_capabilities(self._application_id):
            capability_id = description.capability_id
            if capability_id in candidates_by_id:
                raise ValueError(
                    "capability consumer facade returned duplicate capability ID "
                    f"'{capability_id}' for application '{self._application_id}'"
                )
            availability = availability_by_id.get(capability_id)
            available = availability is not None and availability.available
            reason = None if available else _unavailable_reason(availability)
            candidates_by_id[capability_id] = (
                CapabilityMcpCandidate(
                    name=capability_id,
                    capability_id=capability_id,
                    application_id=self._application_id,
                    title=description.title,
                    description=description.objective,
                    input_schema={"type": "object", "additionalProperties": True},
                    available=available,
                    unavailable_reason=reason,
                )
            )
        return tuple(
            candidate
            for _, candidate in sorted(candidates_by_id.items())
        )

    def invoke(self, name: str, arguments: Mapping[str, object]) -> CapabilityInvocation:
        """Delegate an MCP call unchanged through the consumer facade."""

        return self._consumer.invoke_capability(name, arguments)


def _unavailable_reason(availability: CapabilityAvailability | None) -> str:
    if availability is None:
        return "availability_unknown"
    return availability.reason
