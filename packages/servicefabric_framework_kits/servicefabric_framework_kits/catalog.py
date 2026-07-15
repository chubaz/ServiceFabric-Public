"""The central reviewed FrameworkKitCatalog implementation."""

from __future__ import annotations

from typing import Mapping

from servicefabric_application_model import ModuleDefinition, PrimitiveKind, ValidationError
from servicefabric_framework_kits.definitions import FrameworkKitDefinition
from servicefabric_framework_kits.errors import DuplicateKitRegistration, KitNotFound, PrimitiveMismatch
from servicefabric_framework_kits.identifiers import KitReference, parse_kit_reference
from servicefabric_framework_kits.protocol import FrameworkKitAdapter


class FrameworkKitCatalog:
    """Authority for registering, resolving, and validating ServiceFabric framework kits."""

    def __init__(self) -> None:
        self._kits: dict[tuple[str, str], FrameworkKitDefinition] = {}
        self._adapters: dict[tuple[str, str], FrameworkKitAdapter] = {}

    def register(self, definition: FrameworkKitDefinition, adapter: FrameworkKitAdapter) -> None:
        """Registers a framework kit definition and its planning adapter."""
        key = (definition.reference.kit_id, definition.reference.version)
        if key in self._kits:
            raise DuplicateKitRegistration(
                f"Kit '{definition.reference.kit_id}' version '{definition.reference.version}' "
                "is already registered."
            )
        self._kits[key] = definition
        self._adapters[key] = adapter

    def resolve(self, reference: KitReference) -> tuple[FrameworkKitDefinition, FrameworkKitAdapter]:
        """Resolves a KitReference into its registered definition and planning adapter."""
        key = (reference.kit_id, reference.version)
        if key not in self._kits:
            raise KitNotFound(
                f"Framework kit '{reference.kit_id}' version '{reference.version}' "
                "not found in the catalog."
            )
        return self._kits[key], self._adapters[key]

    def list_for_primitive(self, primitive: PrimitiveKind) -> tuple[FrameworkKitDefinition, ...]:
        """Returns all registered kits supporting a specific primitive, sorted alphabetically."""
        matching_kits = [kit for kit in self._kits.values() if kit.primitive == primitive]
        return tuple(
            sorted(matching_kits, key=lambda x: (x.reference.kit_id, x.reference.version))
        )

    def validate_module(self, module: ModuleDefinition) -> None:
        """Resolves the module's kit and validates it against the kit's constraints.

        Raises:
            PrimitiveMismatch: If the module primitive does not match the kit's primitive.
            ValidationError: If the kit validation fails.
        """
        ref = parse_kit_reference(module.kit)
        definition, adapter = self.resolve(ref)

        if definition.primitive != module.primitive:
            raise PrimitiveMismatch(
                f"Module '{module.module_id}' declares primitive '{module.primitive}', "
                f"but its framework kit '{definition.reference.kit_id}' is configured for primitive '{definition.primitive}'."
            )

        findings = adapter.validate_module(module)
        errors = [f.message for f in findings if f.severity == "error"]
        if errors:
            raise ValidationError(
                f"Module '{module.module_id}' kit validation failed: {'; '.join(errors)}"
            )


# Default pre-registered reviewed catalog instance.
_default_catalog = FrameworkKitCatalog()

# Pre-register reviewed framework kits.
from servicefabric_framework_kits.fastapi_service.adapter import FastAPIServiceAdapter
from servicefabric_framework_kits.fastapi_service.definition import FASTAPI_SERVICE_DEFINITION
from servicefabric_framework_kits.python_library.adapter import PythonLibraryAdapter
from servicefabric_framework_kits.python_library.definition import PYTHON_LIBRARY_DEFINITION
from servicefabric_framework_kits.react_web.adapter import ReactWebAdapter
from servicefabric_framework_kits.react_web.definition import REACT_WEB_DEFINITION

_default_catalog.register(FASTAPI_SERVICE_DEFINITION, FastAPIServiceAdapter())
_default_catalog.register(REACT_WEB_DEFINITION, ReactWebAdapter())
_default_catalog.register(PYTHON_LIBRARY_DEFINITION, PythonLibraryAdapter())


def get_default_catalog() -> FrameworkKitCatalog:
    """Returns the default reviewed FrameworkKitCatalog."""
    return _default_catalog
