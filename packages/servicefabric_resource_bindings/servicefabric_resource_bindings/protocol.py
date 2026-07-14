"""Provider protocol for local resource binding implementations."""

from __future__ import annotations

from typing import Protocol

from servicefabric_resource_bindings.models import BoundResource, ResourceBindingRequest


class ResourceBindingProvider(Protocol):
    """Protocol implemented by local resource binding providers."""

    def can_bind(self, request: ResourceBindingRequest) -> bool:
        """Return whether this provider can bind the request."""

    def bind(self, request: ResourceBindingRequest) -> BoundResource:
        """Return the concrete binding for the request."""
