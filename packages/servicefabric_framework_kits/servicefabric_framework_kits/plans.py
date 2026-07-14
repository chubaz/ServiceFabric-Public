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
class ASGIProcessPlan:
    """Bounded launcher specification for Python ASGI processes."""

    adapter_id: Literal["python-asgi"]
    module_id: str
    working_directory: str
    application_import: str
    reload: bool
    host: Literal["127.0.0.1"] = "127.0.0.1"
    port_binding: Literal["allocated"] = "allocated"
    access_log: bool = True


@dataclass(frozen=True)
class ViteDevelopmentPlan:
    """Bounded development-server description for a reviewed React web module.

    This is declarative only.  Port allocation and process ownership remain with
    the development supervisor.
    """

    adapter_id: Literal["node-vite"]
    module_id: str
    working_directory: str
    host: Literal["127.0.0.1"] = "127.0.0.1"
    port_binding: Literal["allocated"] = "allocated"
    api_base_url_environment: str = "SF_API_BASE_URL"


@dataclass(frozen=True)
class StaticWebRuntimePlan:
    """Static asset handoff for a reviewed React web module.

    The kit identifies the artifact; it does not start or serve it.
    """

    adapter_id: Literal["static-web"]
    module_id: str
    working_directory: str
    assets_directory: str


@dataclass(frozen=True)
class PythonLibraryPreparationPlan:
    """Preparation description for a Python library with no runtime process."""

    adapter_id: Literal["python-library"]
    module_id: str
    working_directory: str
    manifest_path: str = "pyproject.toml"
    test_target: str = "tests"


# Retained as the protocol-facing name for all bounded execution or preparation
# descriptions.  These plans never own a subprocess.
ProcessPlan = (
    ASGIProcessPlan
    | ViteDevelopmentPlan
    | StaticWebRuntimePlan
    | PythonLibraryPreparationPlan
)


@dataclass(frozen=True)
class HealthPlan:
    """Service runtime health monitoring and probe plan."""

    probe_type: Literal["http", "tcp", "process", "none"]
    path: str | None
    timeout_seconds: float


@dataclass(frozen=True)
class KitValidationFinding:
    """Finding produced during framework kit validation of a module."""

    code: str
    severity: Literal["error", "warning"]
    path: str | None
    message: str
