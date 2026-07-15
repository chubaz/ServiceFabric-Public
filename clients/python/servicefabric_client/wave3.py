"""Integration-owned composition for generated Wave-3 applications."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from servicefabric_application_assembly import assemble_application
from servicefabric_application_builder import ApplicationBuildCoordinator
from servicefabric_application_generator import materialize_blueprint
from servicefabric_application_model import load_module_definition_from_file
from servicefabric_agent_guidance import compose_guidance
from servicefabric_artifacts import FileArtifactStore
from servicefabric_blueprints import RESEARCH_NOTES_BLUEPRINT, create_default_blueprint_catalog
from servicefabric_builder.identity import digest, manifest_content_digest
from servicefabric_contracts import ApplicationArtifactManifest
from servicefabric_contracts.metadata import OwnerReference
from servicefabric_framework_kits import KitPlanningContext, get_default_catalog
from servicefabric_process_runtime import (
    HealthTarget,
    ManagedProcessController,
    ResolvedProcessPlan,
    allocate_loopback_port,
)
from servicefabric_workspace import (
    ApplicationAlreadyExists,
    ApplicationLayout,
    WorkspaceContext,
    WorkspaceError,
    WorkspaceService,
)


class Wave3ApplicationService:
    """Composes reviewed Wave-3 APIs without owning specialist business logic."""

    def __init__(self, context: WorkspaceContext):
        self.context = context
        self.workspace = WorkspaceService(context)
        self.catalog = create_default_blueprint_catalog()
        self.controller = ManagedProcessController(context.layout)

    def _layout(self, application_id: str) -> ApplicationLayout:
        return self.workspace.locate_application(application_id)

    def create(self, application_id: str, template: str) -> dict[str, Any]:
        if template != "modular-web-app":
            raise ValueError("only the reviewed modular-web-app template is available")
        blueprint = RESEARCH_NOTES_BLUEPRINT
        applications = self.context.layout.applications
        target = applications / application_id
        if target.exists():
            raise ApplicationAlreadyExists(f"Application directory '{application_id}' already exists on disk.")
        try:
            self.workspace.registry.get(application_id)
        except Exception:
            pass
        else:
            raise ApplicationAlreadyExists(f"Application '{application_id}' is already registered.")

        result = None
        try:
            result = materialize_blueprint(
                blueprint,
                applications,
                application_id,
                blueprint.title,
            )
            layout = self._layout_from_root(application_id, result.root)
            module_kits = {
                module.module_id: str(module.to_manifest()["spec"]["kit"])
                for module in blueprint.modules
            }
            self._write_guidance(layout, module_kits)
            self._write_notes_source(layout)
            record = self.workspace.registry.register(
                application_id=application_id,
                display_name=blueprint.title,
                source_path=f"applications/{application_id}",
            )
        except Exception:
            if result is not None and result.root.exists():
                shutil.rmtree(result.root, ignore_errors=True)
            raise
        return {
            "application_id": record.application_id,
            "template": template,
            "source_path": record.source_path,
            "files": [path.as_posix() for path in result.files],
        }

    @staticmethod
    def _layout_from_root(application_id: str, root: Path) -> ApplicationLayout:
        return ApplicationLayout.from_application_id(application_id, root.parent)

    @staticmethod
    def _write_guidance(layout: ApplicationLayout, module_kits: dict[str, str]) -> None:
        bundle = compose_guidance(module_kits)
        for relative, content in bundle.files.items():
            target = layout.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    @staticmethod
    def _write_notes_source(layout: ApplicationLayout) -> None:
        source = layout.modules / "notes-api"
        source.mkdir(parents=True, exist_ok=True)
        (source / "app.py").write_text(
            """from __future__ import annotations

import sqlite3
from pathlib import Path
from fastapi import FastAPI, Query

app = FastAPI()
DATABASE = Path(__file__).with_name("notes.sqlite3")

def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
    return connection

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/notes")
def create_note(body: str) -> dict[str, object]:
    with _connect() as connection:
        cursor = connection.execute("INSERT INTO notes(body) VALUES (?)", (body,))
        return {"id": cursor.lastrowid, "body": body}

@app.get("/notes/search")
def search_notes(q: str = Query(default="")) -> list[dict[str, object]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, body FROM notes WHERE body LIKE ? ORDER BY id", (f"%{q}%",)
        ).fetchall()
    return [{"id": row[0], "body": row[1]} for row in rows]
""",
            encoding="utf-8",
        )
        (source / "notes.sqlite3").touch()

    def modules(self, application_id: str) -> list[dict[str, Any]]:
        layout = self._layout(application_id)
        modules = []
        for manifest_path in sorted(layout.modules.glob("*/module.yaml")):
            import yaml
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            modules.append({
                "id": manifest["metadata"]["id"],
                "primitive": manifest["spec"]["primitive"],
                "kit": manifest["spec"]["kit"],
                "source": manifest["spec"]["source"],
            })
        return modules

    def validate(self, application_id: str) -> dict[str, Any]:
        layout = self._layout(application_id)
        paths = sorted(layout.modules.glob("*/module.yaml"))
        modules = [load_module_definition_from_file(path) for path in paths]
        assembly = assemble_application(modules)
        workspace = self.workspace.validate()
        if not workspace.valid:
            errors = [finding.message for finding in workspace.findings if finding.severity == "error"]
            raise ValueError("workspace validation failed: " + "; ".join(errors))
        return {"application_id": application_id, "valid": True, "build_order": list(assembly.build_order)}

    def build(self, application_id: str) -> dict[str, Any]:
        layout = self._layout(application_id)
        module_paths = sorted(layout.modules.glob("*/module.yaml"))
        modules = [load_module_definition_from_file(path) for path in module_paths]
        context = KitPlanningContext(
            workspace_root=layout.root,
            state_root=self.context.layout.state,
            artifacts_dir=self.context.layout.artifacts,
            logs_dir=self.context.layout.logs,
        )
        coordinator = ApplicationBuildCoordinator(get_default_catalog(), context)
        plan = coordinator.plan(modules)
        outputs = {item.module_id: Path(item.source_root) for item in plan.modules}
        manifest = coordinator.manifest(plan, outputs)
        files = []
        for module in manifest.modules:
            for item in module.output_files:
                source = outputs[module.module_id] / item.path
                files.append({
                    "path": f"modules/{module.module_id}/{item.path}",
                    "content_digest": item.content_digest,
                    "media_type": "text/plain",
                    "size_bytes": item.size_bytes,
                    "source": source,
                })
        files.sort(key=lambda item: item["path"])
        stable_files = [{key: value for key, value in item.items() if key != "source"} for item in files]
        source_digest = digest([item.source_digest for item in plan.modules])
        build_spec_digest = digest([asdict(item.reviewed_plan) for item in plan.modules])
        stable = {
            "application_id": application_id,
            "application_revision": "0.1.0",
            "builder_id": "servicefabric-wave3-application-builder",
            "builder_revision": "0.1.0",
            "build_spec_digest": build_spec_digest,
            "entry_document": stable_files[0]["path"],
            "files": stable_files,
            "reproducibility": "reproducible",
            "source_digest": source_digest,
            "total_size_bytes": sum(item["size_bytes"] for item in stable_files),
        }
        artifact_digest = digest(stable)
        artifact_id = "artifact." + artifact_digest[7:39]
        artifact = ApplicationArtifactManifest.model_validate({
            "apiVersion": "servicefabric.ai/v1alpha1",
            "kind": "ApplicationArtifactManifest",
            "metadata": {
                "id": artifact_id,
                "name": f"{application_id} 0.1.0",
                "description": "Immutable Wave-3 generated application artifact.",
                "owner_ref": {"kind": "service", "id": "servicefabric-wave3"},
            },
            "spec": {
                **stable,
                "artifact_id": artifact_id,
                "artifact_digest": artifact_digest,
                "provenance": {
                    "source_manifest_ref": f"{application_id}-0.1.0",
                    "source_digest": source_digest,
                    "build_spec_digest": build_spec_digest,
                    "builder_id": stable["builder_id"],
                    "builder_revision": stable["builder_revision"],
                },
            },
        })
        if manifest_content_digest(artifact) != artifact_digest:
            raise ValueError("generated artifact manifest digest is inconsistent")
        store = FileArtifactStore(self.context.layout.artifacts)
        staging = self.context.layout.temporary / f"build-{application_id}"
        shutil.rmtree(staging, ignore_errors=True)
        for item in files:
            target = staging / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item["source"], target)
        store.put_artifact(artifact, staging)
        shutil.rmtree(staging, ignore_errors=True)
        return {
            "application_id": application_id,
            "artifact_id": artifact_id,
            "artifact_digest": artifact_digest,
            "source_digest": source_digest,
            "output_digest": manifest.manifest_digest,
            "modules": list(plan.build_order),
        }

    def _plan(self, application_id: str, module_id: str):
        layout = self._layout(application_id)
        import yaml
        manifest_path = layout.modules / module_id / "module.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        module = load_module_definition_from_file(manifest_path)
        source = layout.root / manifest["spec"]["source"]
        port = allocate_loopback_port()
        return layout, module, source, port

    def prepare(self, application_id: str) -> dict[str, Any]:
        self.validate(application_id)
        return {"application_id": application_id, "state": "prepared"}

    def start(self, application_id: str, module_id: str = "notes-api") -> dict[str, Any]:
        layout, module, source, port = self._plan(application_id, module_id)
        plan = ResolvedProcessPlan(
            application_id=application_id,
            module_id=module_id,
            adapter_id="python-asgi",
            executable=Path(__import__("sys").executable),
            arguments=("-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log"),
            working_directory=source,
            environment=dict(__import__("os").environ),
            log_path=self.context.layout.logs / "applications" / application_id / f"{module_id}.log",
            port=port,
            health_target=HealthTarget("http", f"http://127.0.0.1:{port}/health", 10.0),
            shutdown_timeout_seconds=10.0,
        )
        status = self.controller.start(plan)
        return {"application_id": application_id, "module_id": module_id, "state": status.state, "port": status.port, "health": status.health}

    def status(self, application_id: str, module_id: str = "notes-api") -> dict[str, Any]:
        status = self.controller.status(application_id, module_id)
        return {"application_id": application_id, "module_id": module_id, "state": status.state, "port": status.port, "health": status.health}

    def restart(self, application_id: str, module_id: str) -> dict[str, Any]:
        self.controller.stop(application_id, module_id)
        return self.start(application_id, module_id)

    def stop(self, application_id: str, module_id: str = "notes-api") -> dict[str, Any]:
        status = self.controller.stop(application_id, module_id)
        return {"application_id": application_id, "module_id": module_id, "state": status.state, "port": status.port}
