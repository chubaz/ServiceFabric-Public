"""ServiceFabric local resource binding abstractions."""

from __future__ import annotations

from servicefabric_resource_bindings.catalog import ResourceBindingCatalog
from servicefabric_resource_bindings.errors import (
    DuplicateResourceBinding,
    InvalidResourceBinding,
    ResourceBindingError,
    ResourceBindingNotFound,
    ResourceBindingTypeMismatch,
)
from servicefabric_resource_bindings.identifiers import environment_key_for
from servicefabric_resource_bindings.local import ApplicationLocalBindings
from servicefabric_resource_bindings.models import (
    BoundResource,
    LocalResourceDefinition,
    ResourceBindingPlan,
    ResourceBindingRequest,
)
from servicefabric_resource_bindings.providers import StaticLocalResourceProvider

__all__ = [
    "BoundResource",
    "ApplicationLocalBindings",
    "DuplicateResourceBinding",
    "InvalidResourceBinding",
    "LocalResourceDefinition",
    "ResourceBindingCatalog",
    "ResourceBindingError",
    "ResourceBindingNotFound",
    "ResourceBindingPlan",
    "ResourceBindingRequest",
    "ResourceBindingTypeMismatch",
    "StaticLocalResourceProvider",
    "environment_key_for",
]
