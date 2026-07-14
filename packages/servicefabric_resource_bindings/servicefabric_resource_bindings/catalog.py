"""Catalog for resolving module resource requests to local bindings."""

from __future__ import annotations

from collections.abc import Iterable

from servicefabric_resource_bindings.errors import ResourceBindingNotFound
from servicefabric_resource_bindings.models import (
    BoundResource,
    ResourceBindingPlan,
    ResourceBindingRequest,
)
from servicefabric_resource_bindings.protocol import ResourceBindingProvider


class ResourceBindingCatalog:
    """Ordered registry of local resource binding providers."""

    def __init__(self, providers: Iterable[ResourceBindingProvider] = ()) -> None:
        self._providers = tuple(providers)

    def bind(self, request: ResourceBindingRequest) -> BoundResource:
        """Resolve a single resource request through the first matching provider."""

        for provider in self._providers:
            if provider.can_bind(request):
                return provider.bind(request)
        raise ResourceBindingNotFound(
            f"no local resource binding is registered for '{request.id}'"
        )

    def plan(
        self, module_id: str, requests: Iterable[ResourceBindingRequest]
    ) -> ResourceBindingPlan:
        """Resolve all resource bindings for a module."""

        return ResourceBindingPlan(
            module_id=module_id,
            bindings=tuple(self.bind(request) for request in requests),
        )
