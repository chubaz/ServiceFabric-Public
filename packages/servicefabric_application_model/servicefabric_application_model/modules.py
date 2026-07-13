"""Defines ModuleDefinition models and structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from servicefabric_application_model.interfaces import ProvidedInterface, RequiredInterface
from servicefabric_application_model.lifecycle import LifecycleConfig
from servicefabric_application_model.primitives import PrimitiveKind
from servicefabric_application_model.resources import ResourceRequest


@dataclass(frozen=True)
class ModuleDefinition:
    """Canonical model for a ServiceFabric application module definition."""

    module_id: str
    version: str
    primitive: PrimitiveKind
    kit: str
    source: str
    
    provides_interfaces: tuple[ProvidedInterface, ...] = field(default_factory=tuple)
    requires_interfaces: tuple[RequiredInterface, ...] = field(default_factory=tuple)
    resources: tuple[ResourceRequest, ...] = field(default_factory=tuple)
    lifecycle: LifecycleConfig = field(default_factory=LifecycleConfig)
    
    raw_data: dict[str, Any] = field(default_factory=dict, repr=False)
