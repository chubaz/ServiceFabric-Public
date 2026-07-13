"""Main WorkspaceService façade for all workspace operations."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import yaml

from servicefabric_workspace.errors import (
    ApplicationAlreadyExists,
    ApplicationNotFound,
    InvalidWorkspaceConfiguration,
    WorkspaceError,
    WorkspaceNotInitialized,
)
from servicefabric_workspace.filesystem import check_managed_path_symlink, ensure_descendant
from servicefabric_workspace.identifiers import validate_application_id
from servicefabric_workspace.locking import file_lock
from servicefabric_workspace.models import (
    ApplicationCreateRequest,
    ApplicationLayout,
    ApplicationRecord,
    WorkspaceContext,
    WorkspaceStatus,
    WorkspaceValidation,
)
from servicefabric_workspace.registry import ApplicationRegistry


class WorkspaceService:
    """The public façade coordinating all ServiceFabric workspace and application operations."""

    def __init__(self, context: WorkspaceContext):
        self.context = context
        self.layout = context.layout
        self.registry = ApplicationRegistry(self.layout.registry)

    def initialize(self) -> WorkspaceStatus:
        """Idempotently initialises the workspace.

        Creates visible development directories, hidden platform-state folders,

        and standard configuration metadata.
        """
        if self.context.mode == "legacy-state-only":
            raise WorkspaceError(
                "Operation not supported: cannot initialize a development workspace "
                "in legacy-state-only mode."
            )

        # Acquire initialization file lock to prevent concurrency race conditions
        init_lock_path = self.layout.locks / "workspace-init.lock"
        created = False
        repaired_directories: list[str] = []

        with file_lock(init_lock_path):
            # Check and validate workspace.yaml
            workspace_yaml_path = self.layout.root / "workspace.yaml"
            if workspace_yaml_path.exists():
                if not workspace_yaml_path.is_file():
                    raise InvalidWorkspaceConfiguration("workspace.yaml exists but is not a file.")
                try:
                    with workspace_yaml_path.open("r", encoding="utf-8") as handle:
                        metadata = yaml.safe_load(handle)
                        if not metadata or metadata.get("kind") != "Workspace":
                            raise InvalidWorkspaceConfiguration("Existing workspace.yaml is malformed.")
                except Exception as exc:
                    if not isinstance(exc, InvalidWorkspaceConfiguration):
                        raise InvalidWorkspaceConfiguration(
                            f"Existing workspace.yaml is unparseable: {exc}"
                        ) from exc
                    raise
            else:
                yaml_content = (
                    "apiVersion: servicefabric.local/v1\n"
                    "kind: Workspace\n\n"
                    "metadata:\n"
                    "  id: local-workspace\n"
                    "  name: Local ServiceFabric Workspace\n\n"
                    "spec:\n"
                    "  applicationsDirectory: applications\n"
                    "  recipesDirectory: recipes\n"
                    "  librariesDirectory: libraries\n"
                    "  stateDirectory: .servicefabric\n"
                    "  mode: personal\n"
                )
                workspace_yaml_path.write_text(yaml_content, encoding="utf-8")
                created = True

            # Write .servicefabric/registry/workspace.json
            workspace_json_path = self.layout.registry / "workspace.json"
            if not workspace_json_path.is_file():
                workspace_json_data = {
                    "format": 1,
                    "workspace_id": "local-workspace",
                    "mode": "personal",
                    "local_only": True,
                }
                from servicefabric_workspace.filesystem import atomic_write_text
                atomic_write_text(
                    workspace_json_path,
                    json.dumps(workspace_json_data, indent=2) + "\n",
                )
                created = True

            # Create layout directories idempotently
            directories_to_create = [
                ("applications", self.layout.applications),
                ("recipes", self.layout.recipes),
                ("libraries", self.layout.libraries),
                ("registry", self.layout.registry),
                ("bindings", self.layout.bindings),
                ("resources", self.layout.resources),
                ("runtimes", self.layout.runtimes),
                ("environments", self.layout.environments),
                ("builds", self.layout.builds),
                ("artifacts", self.layout.artifacts),
                ("installations", self.layout.installations),
                ("instances", self.layout.instances),
                ("logs", self.layout.logs),
                ("operations", self.layout.operations),
                ("locks", self.layout.locks),
                ("cache", self.layout.cache),
                ("temporary", self.layout.temporary),
                ("backups", self.layout.backups),
                ("registry_apps", self.layout.registry / "applications"),
            ]

            for name, path in directories_to_create:
                if not path.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                    if not created:
                        repaired_directories.append(name)

        initialized = workspace_yaml_path.is_file()
        
        return WorkspaceStatus(
            initialized=initialized,
            created=created,
            repaired_directories=tuple(repaired_directories),
            root=self.layout.root,
            state=self.layout.state,
            mode=self.context.mode,
        )

    def inspect(self) -> WorkspaceStatus:
        """Inspects the initialization state of the workspace without mutating the filesystem."""
        workspace_yaml_path = self.layout.root / "workspace.yaml"
        initialized = workspace_yaml_path.is_file() and self.layout.state.is_dir()
        
        return WorkspaceStatus(
            initialized=initialized,
            created=False,
            repaired_directories=(),
            root=self.layout.root,
            state=self.layout.state,
            mode=self.context.mode,
        )

    def validate(self) -> WorkspaceValidation:
        """Runs deep (expensive) checks on the workspace layout and schema definitions."""
        from servicefabric_workspace.validation import validate_workspace_deep
        return validate_workspace_deep(self.layout)

    def create_application(self, request: ApplicationCreateRequest) -> ApplicationRecord:
        """Atomically scaffolds a new application project and updates the file-backed registry.

        This operation enforces isolation boundaries, ensuring incomplete state is never left behind.
        """
        if self.context.mode == "legacy-state-only":
            raise WorkspaceError(
                "Operation not supported: cannot create applications in legacy-state-only mode."
            )

        # Enforce that the workspace is initialized
        workspace_yaml_path = self.layout.root / "workspace.yaml"
        if not workspace_yaml_path.is_file():
            raise WorkspaceNotInitialized(
                "Workspace has not been initialized. Run initialize() first."
            )

        app_id = validate_application_id(request.application_id)
        app_layout = ApplicationLayout.from_application_id(app_id, self.layout.applications)

        # Security check: Ensure applications directory is not a symlink
        check_managed_path_symlink(self.layout.applications)
        ensure_descendant(self.layout.applications, app_layout.root)

        # Acquire lock to ensure atomic creation transaction
        app_lock_path = self.layout.locks / f"application-create-{app_id}.lock"
        reg_lock_path = self.layout.locks / f"registry-{app_id}.lock"

        with file_lock(app_lock_path), file_lock(reg_lock_path):
            # Verify destination does not exist
            if app_layout.root.exists():
                raise ApplicationAlreadyExists(
                    f"Application directory '{app_id}' already exists on disk."
                )

            # Verify registry does not contain duplicate entry
            record_path = self.layout.registry / "applications" / f"{app_id}.json"
            if record_path.is_file():
                raise ApplicationAlreadyExists(
                    f"Application '{app_id}' is already registered."
                )

            # Create temporary folder inside the same applications directory (ensuring same filesystem for atomic rename)
            temp_dir_str = tempfile.mkdtemp(
                dir=self.layout.applications, prefix=f".sf-scaffold-tmp-{app_id}-"
            )
            temp_dir = Path(temp_dir_str)

            try:
                # Setup temporary layout
                temp_layout = ApplicationLayout(
                    application_id=app_id,
                    root=temp_dir,
                    metadata=temp_dir / ".servicefabric",
                    modules=temp_dir / "modules",
                    tests=temp_dir / "tests",
                    documentation=temp_dir / "docs",
                    agents_file=temp_dir / "AGENTS.md",
                    readme_file=temp_dir / "README.md",
                    architecture_file=temp_dir / "ARCHITECTURE.md",
                    development_file=temp_dir / "DEVELOPMENT.md",
                    application_definition=temp_dir / ".servicefabric/application.yaml",
                    blueprint=temp_dir / ".servicefabric/blueprint.yaml",
                    bindings=temp_dir / ".servicefabric/bindings.yaml",
                    development_config=temp_dir / ".servicefabric/development.yaml",
                    generated=temp_dir / ".servicefabric/generated",
                    composition_lock=temp_dir / ".servicefabric/application.lock",
                )

                # Generate files inside temp folder
                from servicefabric_workspace.scaffolding import scaffold_application
                scaffold_application(temp_layout, request.display_name)

                # Promote temporary directory to live destination atomically
                try:
                    os.rename(temp_dir, app_layout.root)
                except Exception as exc:
                    raise WorkspaceError(
                        f"Failed to atomically rename temporary application directory: {exc}"
                    ) from exc

                # Update registry record
                relative_source_path = f"applications/{app_id}"
                try:
                    record = self.registry.register(
                        application_id=app_id,
                        display_name=request.display_name,
                        source_path=relative_source_path,
                    )
                except Exception:
                    # Rollback the renamed directory if registration fails
                    if app_layout.root.exists():
                        shutil.rmtree(app_layout.root, ignore_errors=True)
                    raise

                return record

            finally:
                # Cleanup temporary directory if rename did not occur
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)

    def locate_application(self, application_id: str) -> ApplicationLayout:
        """Retrieves and validates the layout paths of a registered application.

        Raises:
            ApplicationNotFound: If the application is not registered or directory is missing.
        """
        app_id = validate_application_id(application_id)
        
        # Check registry
        record = self.registry.get(app_id)

        # Resolve and check filesystem presence
        app_root = (self.layout.root / record.source_path).resolve(strict=False)
        if not app_root.is_dir():
            raise ApplicationNotFound(
                f"Application directory for '{app_id}' not found on disk at {app_root}."
            )

        # Enforce safety rules
        check_managed_path_symlink(app_root)
        ensure_descendant(self.layout.applications, app_root)

        return ApplicationLayout.from_application_id(app_id, self.layout.applications)

    def list_applications(self) -> tuple[ApplicationRecord, ...]:
        """Lists all registered applications in alphabetical order."""
        return self.registry.list()
