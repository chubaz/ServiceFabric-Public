"""Defines the FrameworkKitAdapter Protocol contract."""

from __future__ import annotations

from typing import Protocol, Sequence

from servicefabric_application_model import ModuleDefinition
from servicefabric_framework_kits.plans import (
    BuildPlan,
    DependencyPlan,
    HealthPlan,
    KitPlanningContext,
    KitValidationFinding,
    ProcessPlan,
)


class FrameworkKitAdapter(Protocol):
    """Protocol interface that every framework kit planning adapter must implement."""

    def validate_module(
        self,
        module: ModuleDefinition,
    ) -> Sequence[KitValidationFinding]:
        """Validates that the module definition meets the kit's constraints."""
        ...

    def dependency_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> DependencyPlan:
        """Generates the dependency installation plan."""
        ...

    def build_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> BuildPlan:
        """Generates the immutable build packaging plan."""
        ...

    def development_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> ProcessPlan:
        """Generates the local process execution plan with hot-reloading."""
        ...

    def runtime_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> ProcessPlan:
        """Generates the production process execution plan."""
        ...

    def health_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> HealthPlan:
        """Generates the process monitoring health probe plan."""
        ...
