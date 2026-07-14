"""Declarative preparation adapter for the reviewed Python library kit."""

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
    PythonLibraryPreparationPlan,
)
from servicefabric_framework_kits.validation import require_valid_module


class PythonLibraryAdapter:
    """Describes package preparation for a library that has no process lifecycle."""

    def validate_module(self, module: ModuleDefinition) -> Sequence[KitValidationFinding]:
        if module.primitive != "library":
            raise PrimitiveMismatch(
                f"Framework kit 'python-library' is incompatible with primitive "
                f"'{module.primitive}'. It can only be used with the 'library' primitive."
            )
        return ()

    def dependency_plan(
        self, module: ModuleDefinition, context: KitPlanningContext
    ) -> DependencyPlan:
        require_valid_module(self, module)
        return DependencyPlan(
            ecosystem="python",
            manifest_path="pyproject.toml",
            lockfile_path=None,
            environment_key="PYTHONPATH",
        )

    def build_plan(self, module: ModuleDefinition, context: KitPlanningContext) -> BuildPlan:
        require_valid_module(self, module)
        return BuildPlan(
            adapter_id="python-library-package",
            source_directory=module.source,
            output_directory=str(context.artifacts_dir),
            inputs=("pyproject.toml", "src", "tests"),
        )

    def development_plan(
        self, module: ModuleDefinition, context: KitPlanningContext
    ) -> ProcessPlan:
        require_valid_module(self, module)
        return self._preparation_plan(module)

    def runtime_plan(self, module: ModuleDefinition, context: KitPlanningContext) -> ProcessPlan:
        require_valid_module(self, module)
        return self._preparation_plan(module)

    def health_plan(self, module: ModuleDefinition, context: KitPlanningContext) -> HealthPlan:
        require_valid_module(self, module)
        return HealthPlan(probe_type="none", path=None, timeout_seconds=0.0)

    @staticmethod
    def _preparation_plan(module: ModuleDefinition) -> PythonLibraryPreparationPlan:
        return PythonLibraryPreparationPlan(
            adapter_id="python-library",
            module_id=module.module_id,
            working_directory=module.source,
        )
