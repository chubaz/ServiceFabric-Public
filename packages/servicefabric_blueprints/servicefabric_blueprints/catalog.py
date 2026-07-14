"""Reviewed blueprint catalog implementation."""

from __future__ import annotations

from servicefabric_blueprints.definitions import ApplicationBlueprint
from servicefabric_blueprints.errors import BlueprintNotFound, DuplicateBlueprintRegistration


class BlueprintCatalog:
    """Authority for registering and resolving reviewed application blueprints."""

    def __init__(self) -> None:
        self._blueprints: dict[tuple[str, str], ApplicationBlueprint] = {}

    def register(self, blueprint: ApplicationBlueprint) -> None:
        """Registers a blueprint by immutable ID and version."""
        key = (blueprint.blueprint_id, blueprint.version)
        if key in self._blueprints:
            raise DuplicateBlueprintRegistration(
                f"Blueprint '{blueprint.blueprint_id}' version '{blueprint.version}' "
                "is already registered."
            )
        blueprint.load_modules()
        self._blueprints[key] = blueprint

    def resolve(self, blueprint_id: str, version: str) -> ApplicationBlueprint:
        """Resolves an exact blueprint ID and version."""
        key = (blueprint_id, version)
        if key not in self._blueprints:
            raise BlueprintNotFound(
                f"Blueprint '{blueprint_id}' version '{version}' not found in the catalog."
            )
        return self._blueprints[key]

    def list(self) -> tuple[ApplicationBlueprint, ...]:
        """Returns registered blueprints sorted deterministically."""
        return tuple(
            self._blueprints[key]
            for key in sorted(self._blueprints)
        )
