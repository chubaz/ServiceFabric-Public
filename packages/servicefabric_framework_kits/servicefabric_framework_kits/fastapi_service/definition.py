"""Metadata definition for the fastapi-service framework kit."""

from __future__ import annotations

from servicefabric_framework_kits.definitions import FrameworkKitDefinition
from servicefabric_framework_kits.identifiers import KitReference

FASTAPI_SERVICE_DEFINITION = FrameworkKitDefinition(
    reference=KitReference(
        kit_id="fastapi-service",
        version="1.0.0",
    ),
    primitive="service",
    adapter_id="reviewed-fastapi-v1",
    runtime_family="python",
    development_supported=True,
    build_supported=True,
    runtime_supported=True,
)
