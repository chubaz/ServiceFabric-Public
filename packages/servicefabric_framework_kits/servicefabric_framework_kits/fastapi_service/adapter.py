"""Planning adapter implementation for the fastapi-service framework kit."""

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
)


class FastAPIServiceAdapter:
    """Planning adapter that translates a module using the fastapi-service kit into typed plans."""

    def validate_module(
        self,
        module: ModuleDefinition,
    ) -> Sequence[KitValidationFinding]:
        """Validates module primitive compatibility and key fields."""
        findings: list[KitValidationFinding] = []
        
        # Enforce service primitive compatibility
        if module.primitive != "service":
            raise PrimitiveMismatch(
                f"Framework kit 'fastapi-service' is incompatible with primitive '{module.primitive}'. "
                "It can only be used with the 'service' primitive."
            )

        if not module.source:
            findings.append(
                KitValidationFinding(
                    code="missing_source",
                    severity="error",
                    path="spec.source",
                    message="Required source directory path is missing.",
                )
            )

        # Enforce that no raw/unrestricted shell commands are supplied
        if module.raw_data and "spec" in module.raw_data:
            spec_data = module.raw_data["spec"]
            if "command" in spec_data or "shell" in spec_data:
                findings.append(
                    KitValidationFinding(
                        code="unrestricted_command",
                        severity="error",
                        path="spec.command",
                        message="Arbitrary or unrestricted shell commands are not permitted.",
                    )
                )

        return findings

    def dependency_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> DependencyPlan:
        """Generates Python/Pip packaging dependency installation plans."""
        self.validate_module(module)
        return DependencyPlan(
            ecosystem="python",
            manifest_path="pyproject.toml",
            lockfile_path="poetry.lock",
            environment_key="PYTHONPATH",
        )

    def build_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> BuildPlan:
        """Generates standard Python package builder plan."""
        self.validate_module(module)
        return BuildPlan(
            adapter_id="python-package",
            source_directory=str(module.source),
            output_directory=str(context.artifacts_dir),
            inputs=("app", "pyproject.toml"),
        )

    def development_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> ProcessPlan:
        """Generates development process plan with hot-reloading enabled."""
        self.validate_module(module)
        return ProcessPlan(
            adapter_id="python-asgi",
            module_id=module.module_id,
            working_directory=str(module.source),
            entrypoint="uvicorn",
            arguments=("app.main:app", "--reload", "--host", "127.0.0.1"),
            environment_keys=("PYTHONPATH", "SF_MODULE_PORT"),
            needs_allocated_port=True,
        )

    def runtime_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> ProcessPlan:
        """Generates runtime process plan for production-like execution."""
        self.validate_module(module)
        return ProcessPlan(
            adapter_id="python-asgi",
            module_id=module.module_id,
            working_directory=str(module.source),
            entrypoint="uvicorn",
            arguments=("app.main:app", "--host", "127.0.0.1"),
            environment_keys=("PYTHONPATH", "SF_MODULE_PORT"),
            needs_allocated_port=True,
        )

    def health_plan(
        self,
        module: ModuleDefinition,
        context: KitPlanningContext,
    ) -> HealthPlan:
        """Generates HTTP-probe health plan based on module configuration."""
        self.validate_module(module)
        probe_path = "/health"
        if module.lifecycle.readiness and module.lifecycle.readiness.path:
            probe_path = module.lifecycle.readiness.path
        return HealthPlan(
            probe_type="http",
            path=probe_path,
            timeout_seconds=10.0,
        )
