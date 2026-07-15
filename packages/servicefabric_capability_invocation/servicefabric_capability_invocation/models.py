"""Immutable values and ports for transport-neutral capability invocation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from servicefabric_operation_model import HttpBinding, OperationDefinition


@dataclass(frozen=True)
class CapabilityAvailability:
    """The derived live endpoint view consumed by canonical invocation."""

    available: bool
    endpoint: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class CapabilityInvocationRequest:
    """A request to invoke one statically registered capability."""

    capability_id: str
    input: Any
    binding_id: str | None = None


@dataclass(frozen=True)
class TransportInvocation:
    """The fully resolved request handed to a transport adapter."""

    capability_id: str
    operation: OperationDefinition
    binding: HttpBinding
    endpoint: str
    input: Any


@dataclass(frozen=True)
class CapabilityInvocationResult:
    """The validated response together with its deterministic resolution chain."""

    capability_id: str
    operation_id: str
    binding_id: str
    output: Any


class OperationResolver(Protocol):
    def resolve_operation(self, operation_id: str) -> OperationDefinition:
        """Return the reviewed operation definition for an exact identifier."""


class AvailabilityResolver(Protocol):
    def resolve_availability(self, capability_id: str) -> CapabilityAvailability:
        """Return the current derived availability for an exact capability."""


class SchemaResolver(Protocol):
    def resolve_schema(self, schema_ref: str) -> Mapping[str, Any]:
        """Return the reviewed JSON Schema associated with an exact reference."""


class TransportAdapter(Protocol):
    def invoke(self, request: TransportInvocation) -> Any:
        """Perform an already-resolved request without adding business logic."""
