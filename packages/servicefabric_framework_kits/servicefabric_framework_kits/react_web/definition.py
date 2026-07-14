"""Metadata definition for the reviewed React web kit."""

from __future__ import annotations

from servicefabric_framework_kits.definitions import FrameworkKitDefinition
from servicefabric_framework_kits.identifiers import KitReference


REACT_WEB_DEFINITION = FrameworkKitDefinition(
    reference=KitReference(kit_id="react-web", version="1.0.0"),
    primitive="web",
    adapter_id="reviewed-react-v1",
    runtime_family="node",
    development_supported=True,
    build_supported=True,
    runtime_supported=True,
)
