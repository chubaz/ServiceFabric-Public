"""Declarative planning adapter for the reviewed React web kit."""

from __future__ import annotations

from typing import Sequence

from servicefabric_application_model import ModuleDefinition
from servicefabric_framework_kits.errors import PrimitiveMismatch
from servicefabric_framework_kits.plans import (
    BuildPlan,
    DependencyPlan,
    HealthPlan,
    KitPlanningContext,
    KitValidationFinding,
    ProcessPlan,
    StaticWebRuntimePlan,
    ViteDevelopmentPlan,
)
from servicefabric_framework_kits.validation import require_valid_module


class ReactWebAdapter:
    """Produces bounded Vite and static-asset plans; it never launches them."""

    def validate_module(self, module: ModuleDefinition) -> Sequence[KitValidationFinding]:
        if module.primitive != "web":
            raise PrimitiveMismatch(
                f"Framework kit 'react-web' is incompatible with primitive "
                f"'{module.primitive}'. It can only be used with the 'web' primitive."
            )
        return ()

    def dependency_plan(
        self, module: ModuleDefinition, context: KitPlanningContext
    ) -> DependencyPlan:
        require_valid_module(self, module)
        return DependencyPlan(
            ecosystem="node",
            manifest_path="package.json",
            lockfile_path="package-lock.json",
            environment_key="SF_API_BASE_URL",
        )

    def build_plan(self, module: ModuleDefinition, context: KitPlanningContext) -> BuildPlan:
        require_valid_module(self, module)
        return BuildPlan(
            adapter_id="vite-static-assets",
            source_directory=module.source,
            output_directory=str(context.artifacts_dir),
            inputs=("package.json", "src"),
        )

    def development_plan(
        self, module: ModuleDefinition, context: KitPlanningContext
    ) -> ProcessPlan:
        require_valid_module(self, module)
        return ViteDevelopmentPlan(
            adapter_id="node-vite",
            module_id=module.module_id,
            working_directory=module.source,
        )

    def runtime_plan(self, module: ModuleDefinition, context: KitPlanningContext) -> ProcessPlan:
        require_valid_module(self, module)
        return StaticWebRuntimePlan(
            adapter_id="static-web",
            module_id=module.module_id,
            working_directory=module.source,
            assets_directory=str(context.artifacts_dir),
        )

    def health_plan(self, module: ModuleDefinition, context: KitPlanningContext) -> HealthPlan:
        require_valid_module(self, module)
        return HealthPlan(probe_type="http", path="/", timeout_seconds=10.0)
