"""Immutable models for local resource binding declarations and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from servicefabric_application_model import ResourceRequest


@dataclass(frozen=True)
class ResourceBindingRequest:
    """Resource request normalized for binding resolution."""

    id: str
    type: str
    scope: str = "application"

    @classmethod
    def from_application_request(
        cls, request: ResourceRequest
    ) -> "ResourceBindingRequest":
        """Create a binding request from the canonical application model."""

        return cls(id=request.id, type=request.type, scope=request.scope)


@dataclass(frozen=True)
class LocalResourceDefinition:
    """Reviewed local resource definition available to development modules."""

    id: str
    type: str
    scope: str = "application"
    provider_id: str = "static-local"
    endpoint: str | None = None
    environment: Mapping[str, str] = field(default_factory=dict)
    secret_refs: Mapping[str, str] = field(default_factory=dict)
    readiness: str = "ready"


@dataclass(frozen=True)
class BoundResource:
    """Concrete local binding values safe for process environment injection."""

    id: str
    type: str
    scope: str
    provider_id: str
    environment: Mapping[str, str]
    secret_refs: Mapping[str, str]
    readiness: str


@dataclass(frozen=True)
class ResourceBindingPlan:
    """All local resource bindings resolved for one module."""

    module_id: str
    bindings: tuple[BoundResource, ...]

    @property
    def environment(self) -> dict[str, str]:
        """Flatten non-secret environment values for module launchers."""

        values: dict[str, str] = {}
        for binding in self.bindings:
            values.update(binding.environment)
        return values

    @property
    def secret_refs(self) -> dict[str, str]:
        """Flatten opaque secret references by environment key."""

        values: dict[str, str] = {}
        for binding in self.bindings:
            values.update(binding.secret_refs)
        return values
