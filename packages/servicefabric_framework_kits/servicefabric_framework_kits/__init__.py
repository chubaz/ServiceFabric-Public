"""ServiceFabric Framework Kit Catalog and Adapter Library."""

from __future__ import annotations

from servicefabric_framework_kits.definitions import FrameworkKitDefinition
from servicefabric_framework_kits.errors import (
    DuplicateKitRegistration,
    InvalidKitReference,
    KitError,
    KitNotFound,
    PrimitiveMismatch,
    KitValidationError,
)
from servicefabric_framework_kits.identifiers import KitReference, parse_kit_reference
from servicefabric_framework_kits.catalog import FrameworkKitCatalog, get_default_catalog
from servicefabric_framework_kits.plans import (
    BuildPlan,
    DependencyPlan,
    HealthPlan,
    KitPlanningContext,
    KitValidationFinding,
    ProcessPlan,
    ASGIProcessPlan,
    ViteDevelopmentPlan,
    StaticWebRuntimePlan,
    PythonLibraryPreparationPlan,
)
from servicefabric_framework_kits.protocol import FrameworkKitAdapter
from servicefabric_framework_kits.validation import require_valid_module

__all__ = [
    "FrameworkKitDefinition",
    "DuplicateKitRegistration",
    "InvalidKitReference",
    "KitError",
    "KitNotFound",
    "PrimitiveMismatch",
    "KitValidationError",
    "KitReference",
    "parse_kit_reference",
    "FrameworkKitCatalog",
    "get_default_catalog",
    "BuildPlan",
    "DependencyPlan",
    "HealthPlan",
    "KitPlanningContext",
    "KitValidationFinding",
    "ProcessPlan",
    "ASGIProcessPlan",
    "ViteDevelopmentPlan",
    "StaticWebRuntimePlan",
    "PythonLibraryPreparationPlan",
    "FrameworkKitAdapter",
    "require_valid_module",
]
