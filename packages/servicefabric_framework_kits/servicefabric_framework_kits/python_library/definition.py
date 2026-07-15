"""Metadata definition for the reviewed Python library kit."""

from __future__ import annotations

from servicefabric_framework_kits.definitions import FrameworkKitDefinition
from servicefabric_framework_kits.identifiers import KitReference


PYTHON_LIBRARY_DEFINITION = FrameworkKitDefinition(
    reference=KitReference(kit_id="python-library", version="1.0.0"),
    primitive="library",
    adapter_id="reviewed-python-library-v1",
    runtime_family="python",
    development_supported=False,
    build_supported=True,
    runtime_supported=False,
)
