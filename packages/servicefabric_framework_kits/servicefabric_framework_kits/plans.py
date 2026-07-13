"""Typed plans produced by framework kit planning adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class KitPlanningContext:
    """Provides path resolution parameters for kit planning."""

    workspace_root: Path
    state_root: Path
    artifacts_dir: Path
    logs_dir: Path


@dataclass(frozen=True)
class DependencyPlan:
    """Ecosystem dependency installation plan."""

    ecosystem: Literal["python", "node"]
    manifest_path: str
    lockfile_path: str | None
    environment_key: str


@dataclass(frozen=True)
class BuildPlan:
    """Immutable asset build/packaging plan."""

    adapter_id: str
    source_directory: str
    output_directory: str
    inputs: tuple[str, ...]


@dataclass(frozen=True)
class ProcessPlan:
    """Service or process runtime execution plan."""

    adapter_id: str
    module_id: str
    working_directory: str
    entrypoint: str
    arguments: tuple[str, ...]
    environment_keys: tuple[str, ...]
    needs_allocated_port: bool


@dataclass(frozen=True)
class HealthPlan:
    """Service runtime health monitoring and probe plan."""

    probe_type: Literal["http", "tcp", "process"]
    path: str | None
    timeout_seconds: float


@dataclass(frozen=True)
class KitValidationFinding:
    """Finding produced during framework kit validation of a module."""

    code: str
    severity: Literal["error", "warning"]
    path: str | None
    message: str
