"""ServiceFabric Module and Primitive Configuration Model."""

from __future__ import annotations

from servicefabric_application_model.errors import (
    DependencyError,
    InvalidModuleDefinition,
    InvalidPrimitive,
    ModelError,
    ValidationError,
)
from servicefabric_application_model.interfaces import ProvidedInterface, RequiredInterface
from servicefabric_application_model.lifecycle import LifecycleConfig, ReadinessProbe, ShutdownConfig
from servicefabric_application_model.loader import (
    load_module_definition_from_dict,
    load_module_definition_from_file,
)
from servicefabric_application_model.modules import ModuleDefinition, ResourceExpectations
from servicefabric_application_model.primitives import VALID_PRIMITIVES, PrimitiveKind, validate_primitive
from servicefabric_application_model.resources import ResourceRequest
from servicefabric_application_model.validation import validate_module_graph

__all__ = [
    "DependencyError",
    "InvalidModuleDefinition",
    "InvalidPrimitive",
    "ModelError",
    "ValidationError",
    "ProvidedInterface",
    "RequiredInterface",
    "LifecycleConfig",
    "ReadinessProbe",
    "ShutdownConfig",
    "load_module_definition_from_dict",
    "load_module_definition_from_file",
    "ModuleDefinition",
    "ResourceExpectations",
    "VALID_PRIMITIVES",
    "PrimitiveKind",
    "validate_primitive",
    "ResourceRequest",
    "validate_module_graph",
]
