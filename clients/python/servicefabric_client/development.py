"""Integration composition for the local Research Notes development runtime."""

from __future__ import annotations

import dataclasses
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path

from servicefabric_application_assembly import ApplicationAssembly, ApplicationResource, load_application_assembly_from_files
from servicefabric_application_dev_supervisor import ApplicationDevelopmentSupervisor
from servicefabric_framework_kits import (
    ASGIProcessPlan,
    KitPlanningContext,
    PythonLibraryPreparationPlan,
    StaticWebRuntimePlan,
    ViteDevelopmentPlan,
    get_default_catalog,
    parse_kit_reference,
)
from servicefabric_process_runtime import HealthTarget, ManagedProcessController, ProcessPlanResolver, ResolvedProcessPlan, allocate_loopback_port
from servicefabric_resource_bindings import ApplicationLocalBindings, ResourceBindingRequest
from servicefabric_workspace import ApplicationLayout, WorkspaceLayout
from servicefabric_workspace.filesystem import atomic_write_text


APPLICATION_ID = "research-notes"


class _LocalResourceLifecycle:
    """Supervisor resource protocol backed by the accepted local provider."""

    def __init__(self, workspace: WorkspaceLayout) -> None:
        self._workspace = workspace
        self._bindings = ApplicationLocalBindings(APPLICATION_ID, workspace.bindings / APPLICATION_ID)
        self._prepared = False

    def prepare(self, application_id: str, resources: Mapping[str, ApplicationResource]) -> Mapping[str, str]:
        if application_id != APPLICATION_ID:
            raise ValueError(f"unknown development application '{application_id}'")
        requests = tuple(
            ResourceBindingRequest(id=item.id, type=item.type, scope=item.scope)
            for _, item in sorted(resources.items())
        )
        environment: dict[str, str] = {}
        for bound in self._bindings.resolve(requests):
            environment.update(bound.environment)
        # Research Notes consumes the logical database binding through its public API name.
        if "SF_NOTES_DB_URL" in environment:
            environment["SF_DATABASE_PRIMARY_URL"] = environment["SF_NOTES_DB_URL"]
        self._prepared = True
        self._persist(environment)
        return dict(sorted(environment.items()))

    def release(self, application_id: str, resource_ids: tuple[str, ...]) -> None:
        if application_id != APPLICATION_ID:
            raise ValueError(f"unknown development application '{application_id}'")
        self._bindings.release()
        self._prepared = False

    def status(self, application_id: str, resource_id: str) -> str:
        if application_id != APPLICATION_ID:
            return "unavailable"
        state = self._workspace.bindings / APPLICATION_ID / "resolved-bindings.json"
        return "ready" if state.is_file() else "unavailable"

    def _persist(self, environment: Mapping[str, str]) -> None:
        atomic_write_text(
            self._workspace.bindings / APPLICATION_ID / "development-environment.json",
            json.dumps({"application_id": APPLICATION_ID, "environment": dict(environment)}, sort_keys=True, indent=2) + "\n",
        )


class ResearchNotesDevelopmentService:
    """Composes accepted Wave-2 public interfaces for one local application."""

    def __init__(self, workspace: WorkspaceLayout, repository_root: Path | None = None) -> None:
        self.workspace = workspace
        self.repository_root = (repository_root or Path(__file__).resolve().parents[3]).resolve()
        self.source_root = self.repository_root / "examples" / APPLICATION_ID
        if not self.source_root.is_dir():
            raise ValueError(f"Research Notes source is unavailable at {self.source_root}")
        self.assembly = self._load_assembly()
        self.application = self._application_layout()
        self.resources = _LocalResourceLifecycle(workspace)
        self.processes = ManagedProcessController(workspace)
        self._plans: dict[str, ResolvedProcessPlan | None] = {}
        self._prepared_modules: list[str] = []
        self.supervisor = ApplicationDevelopmentSupervisor(
            self.assembly,
            self.processes,
            self.resources,
            self._prepare_module,
            self._create_plan,
        )

    def prepare(self) -> dict[str, object]:
        status = self.supervisor.prepare(APPLICATION_ID)
        return self._status_value(status)

    def start(self) -> dict[str, object]:
        return self._status_value(self.supervisor.start(APPLICATION_ID))

    def status(self) -> dict[str, object]:
        return self._status_value(self.supervisor.status(APPLICATION_ID))

    def restart(self, module_id: str) -> dict[str, object]:
        return dataclasses.asdict(self.supervisor.restart(APPLICATION_ID, module_id))

    def stop(self) -> dict[str, object]:
        return self._status_value(self.supervisor.stop(APPLICATION_ID))

    def _load_assembly(self) -> ApplicationAssembly:
        manifests = tuple(sorted(self.source_root.glob("*/module.yaml")))
        if len(manifests) != 3:
            raise ValueError("Research Notes must declare exactly three module manifests")
        assembly = load_application_assembly_from_files(manifests)
        atomic_write_text(
            self.workspace.builds / APPLICATION_ID / "assembly.json",
            json.dumps(
                {
                    "application_id": APPLICATION_ID,
                    "build_order": assembly.build_order,
                    "startup_order": assembly.startup_order,
                    "shutdown_order": assembly.shutdown_order,
                    "resources": {key: dataclasses.asdict(value) for key, value in assembly.resources_by_id.items()},
                },
                sort_keys=True,
                indent=2,
            ) + "\n",
        )
        return assembly

    def _application_layout(self) -> ApplicationLayout:
        metadata = self.workspace.state / "applications" / APPLICATION_ID
        return ApplicationLayout(
            application_id=APPLICATION_ID,
            root=self.repository_root,
            metadata=metadata,
            modules=self.source_root,
            tests=self.source_root / "tests",
            documentation=self.source_root / "docs",
            agents_file=self.source_root / "AGENTS.md",
            readme_file=self.source_root / "README.md",
            architecture_file=self.source_root / "ARCHITECTURE.md",
            development_file=self.source_root / "DEVELOPMENT.md",
            application_definition=self.source_root / "application.yaml",
            blueprint=metadata / "blueprint.yaml",
            bindings=metadata / "bindings.yaml",
            development_config=metadata / "development.yaml",
            generated=metadata / "generated",
            composition_lock=metadata / "application.lock",
        )

    def _context(self) -> KitPlanningContext:
        return KitPlanningContext(
            workspace_root=self.repository_root,
            state_root=self.workspace.state,
            artifacts_dir=self.workspace.artifacts / APPLICATION_ID,
            logs_dir=self.workspace.logs / "applications" / APPLICATION_ID,
        )

    def _prepare_module(self, node: object, bindings: Mapping[str, str]) -> None:
        module = node.module  # type: ignore[attr-defined]
        definition, adapter = get_default_catalog().resolve(parse_kit_reference(module.kit))
        if definition.primitive != module.primitive:
            raise ValueError(f"kit primitive mismatch for '{module.module_id}'")
        adapter.validate_module(module)
        plan = adapter.development_plan(module, self._context())
        self._prepared_modules.append(module.module_id)
        atomic_write_text(
            self.workspace.builds / APPLICATION_ID / "plans" / f"{module.module_id}.json",
            json.dumps({"module_id": module.module_id, "plan": dataclasses.asdict(plan)}, sort_keys=True, indent=2) + "\n",
        )

    def _create_plan(self, node: object, bindings: Mapping[str, str]) -> ResolvedProcessPlan | None:
        module = node.module  # type: ignore[attr-defined]
        if module.module_id in self._plans:
            return self._plans[module.module_id]
        _, adapter = get_default_catalog().resolve(parse_kit_reference(module.kit))
        process_plan = adapter.development_plan(module, self._context())
        health_plan = adapter.health_plan(module, self._context())
        if isinstance(process_plan, PythonLibraryPreparationPlan):
            self._plans[module.module_id] = None
            return None
        if isinstance(process_plan, ASGIProcessPlan):
            resolved = ProcessPlanResolver().resolve(
                application=self.application,
                module=module,
                process_plan=process_plan,
                health_plan=health_plan,
                workspace=self.workspace,
            )
            environment = dict(resolved.environment)
            environment.update(bindings)
            domain_path = self.repository_root / "examples" / APPLICATION_ID / "domain"
            environment["PYTHONPATH"] = os.pathsep.join((str(domain_path), environment["PYTHONPATH"]))
            self._plans[module.module_id] = dataclasses.replace(resolved, environment=environment)
            return self._plans[module.module_id]
        if isinstance(process_plan, (ViteDevelopmentPlan, StaticWebRuntimePlan)):
            port = allocate_loopback_port()
            environment = dict(os.environ)
            environment.update(bindings)
            api_plan = self._plans.get("notes-api")
            if api_plan and api_plan.port:
                environment["SF_API_BASE_URL"] = f"http://127.0.0.1:{api_plan.port}"
            log_path = self.workspace.logs / "applications" / APPLICATION_ID / f"{module.module_id}.log"
            self._plans[module.module_id] = ResolvedProcessPlan(
                application_id=APPLICATION_ID,
                module_id=module.module_id,
                adapter_id="reviewed-react-static-web",
                executable=Path(sys.executable),
                arguments=(
                    str(Path(__file__).with_name("static_web_server.py")), "--root", str(self.repository_root / module.source),
                    "--host", "127.0.0.1", "--port", str(port),
                ),
                working_directory=self.repository_root / module.source,
                environment=environment,
                log_path=log_path,
                port=port,
                health_target=HealthTarget("http", f"http://127.0.0.1:{port}/health", 10.0),
                shutdown_timeout_seconds=float(module.lifecycle.shutdown.timeout_seconds),
            )
            return self._plans[module.module_id]
        raise ValueError(f"unsupported reviewed process plan for '{module.module_id}'")

    @staticmethod
    def _status_value(status: object) -> dict[str, object]:
        value = dataclasses.asdict(status)
        return json.loads(json.dumps(value, sort_keys=True))
