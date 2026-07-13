"""Workspace data models and structures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class WorkspaceLayout:
    root: Path
    state: Path

    applications: Path
    recipes: Path
    libraries: Path

    registry: Path
    bindings: Path
    resources: Path
    runtimes: Path
    environments: Path
    builds: Path
    artifacts: Path
    installations: Path
    instances: Path
    logs: Path
    operations: Path
    locks: Path
    cache: Path
    temporary: Path
    backups: Path

    @classmethod
    def from_root(cls, root: Path, state: Path | None = None) -> WorkspaceLayout:
        """Constructs a WorkspaceLayout from a root directory and optional state directory."""
        state_dir = state if state is not None else root / ".servicefabric"
        return cls(
            root=root,
            state=state_dir,
            applications=root / "applications",
            recipes=root / "recipes",
            libraries=root / "libraries",
            registry=state_dir / "registry",
            bindings=state_dir / "bindings",
            resources=state_dir / "resources",
            runtimes=state_dir / "runtimes",
            environments=state_dir / "environments",
            builds=state_dir / "builds",
            artifacts=state_dir / "artifacts",
            installations=state_dir / "installations",
            instances=state_dir / "instances",
            logs=state_dir / "logs",
            operations=state_dir / "operations",
            locks=state_dir / "locks",
            cache=state_dir / "cache",
            temporary=state_dir / "tmp",
            backups=state_dir / "backups",
        )

    # Compatibility properties for legacy state directory structures
    @property
    def config(self) -> Path:
        return self.state / "config"

    @property
    def approvals(self) -> Path:
        return self.state / "approvals"

    @property
    def legacy_hosted_applications(self) -> Path:
        return self.state / "hosted-applications"


@dataclass(frozen=True)
class ApplicationLayout:
    application_id: str
    root: Path

    metadata: Path
    modules: Path
    tests: Path
    documentation: Path

    agents_file: Path
    readme_file: Path
    architecture_file: Path
    development_file: Path

    application_definition: Path
    blueprint: Path
    bindings: Path
    development_config: Path
    generated: Path
    composition_lock: Path

    @classmethod
    def from_application_id(cls, application_id: str, applications_dir: Path) -> ApplicationLayout:
        """Constructs an ApplicationLayout for a specific application ID under applications_dir."""
        app_root = applications_dir / application_id
        sf_dir = app_root / ".servicefabric"
        return cls(
            application_id=application_id,
            root=app_root,
            metadata=sf_dir,
            modules=app_root / "modules",
            tests=app_root / "tests",
            documentation=app_root / "docs",
            agents_file=app_root / "AGENTS.md",
            readme_file=app_root / "README.md",
            architecture_file=app_root / "ARCHITECTURE.md",
            development_file=app_root / "DEVELOPMENT.md",
            application_definition=sf_dir / "application.yaml",
            blueprint=sf_dir / "blueprint.yaml",
            bindings=sf_dir / "bindings.yaml",
            development_config=sf_dir / "development.yaml",
            generated=sf_dir / "generated",
            composition_lock=sf_dir / "application.lock",
        )


@dataclass(frozen=True)
class WorkspaceContext:
    layout: WorkspaceLayout
    mode: Literal["external", "legacy-state-only"]
    resolution_source: Literal[
        "explicit",
        "environment",
        "current-directory",
        "legacy-home",
    ]


@dataclass(frozen=True)
class WorkspaceStatus:
    initialized: bool
    created: bool
    repaired_directories: tuple[str, ...]
    root: Path
    state: Path
    mode: str


@dataclass(frozen=True)
class ApplicationCreateRequest:
    application_id: str
    display_name: str


@dataclass(frozen=True)
class ApplicationRecord:
    application_id: str
    display_name: str
    source_path: str
    status: str


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    severity: Literal["error", "warning"]
    path: Path | None
    message: str


@dataclass(frozen=True)
class WorkspaceValidation:
    valid: bool
    findings: tuple[ValidationFinding, ...]


@dataclass(frozen=True)
class ApplicationHostPaths:
    root: Path
    artifacts: Path
    locks: Path
    logs: Path
