"""Definitions for static framework kit metadata."""

from __future__ import annotations

from dataclasses import dataclass

from servicefabric_application_model import PrimitiveKind
from servicefabric_framework_kits.identifiers import KitReference


@dataclass(frozen=True)
class FrameworkKitDefinition:
    """Immutable metadata description of a framework kit."""

    reference: KitReference
    primitive: PrimitiveKind
    adapter_id: str
    runtime_family: str
    development_supported: bool
    build_supported: bool
    runtime_supported: bool
