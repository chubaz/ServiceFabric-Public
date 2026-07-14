"""Immutable reviewed application blueprint definitions."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from servicefabric_application_model import (
    ModuleDefinition,
    load_module_definition_from_dict,
    validate_module_graph,
)
from servicefabric_framework_kits import FrameworkKitCatalog, get_default_catalog


@dataclass(frozen=True)
class BlueprintModule:
    """A reviewed module manifest embedded in an application blueprint."""

    module_id: str
    manifest: Mapping[str, Any]

    @classmethod
    def from_manifest(cls, manifest: Mapping[str, Any]) -> "BlueprintModule":
        """Creates a blueprint module from a strict ApplicationModule manifest."""
        module = load_module_definition_from_dict(dict(deepcopy(manifest)))
        return cls(
            module_id=module.module_id,
            manifest=MappingProxyType(dict(deepcopy(manifest))),
        )

    def to_manifest(self) -> dict[str, Any]:
        """Returns a caller-owned manifest dictionary."""
        return dict(deepcopy(dict(self.manifest)))


@dataclass(frozen=True)
class ApplicationBlueprint:
    """A deterministic, reviewed application module graph template."""

    blueprint_id: str
    version: str
    title: str
    description: str
    modules: tuple[BlueprintModule, ...]

    def module_manifests(self) -> tuple[dict[str, Any], ...]:
        """Returns caller-owned ApplicationModule manifests in blueprint order."""
        return tuple(module.to_manifest() for module in self.modules)

    def load_modules(
        self,
        kit_catalog: FrameworkKitCatalog | None = None,
    ) -> tuple[ModuleDefinition, ...]:
        """Loads and validates blueprint modules against model, graph, and kit rules."""
        catalog = kit_catalog or get_default_catalog()
        modules = tuple(
            load_module_definition_from_dict(manifest)
            for manifest in self.module_manifests()
        )
        validate_module_graph(list(modules))
        for module in modules:
            catalog.validate_module(module)
        return modules

    def module_manifest(self, module_id: str) -> dict[str, Any]:
        """Returns a caller-owned manifest for a blueprint module ID."""
        for module in self.modules:
            if module.module_id == module_id:
                return module.to_manifest()
        raise KeyError(f"Blueprint '{self.blueprint_id}' has no module '{module_id}'.")
