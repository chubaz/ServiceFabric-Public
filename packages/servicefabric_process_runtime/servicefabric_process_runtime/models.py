"""Runtime process data models, statuses, and resource snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping


@dataclass(frozen=True)
class HealthTarget:
    """Target details used for health probing."""

    probe_type: Literal["http", "tcp", "process"]
    url: str | None = None
    timeout_seconds: float = 10.0


@dataclass(frozen=True)
class ResolvedProcessPlan:
    """Fully resolved, machine-specific, executable process execution plan."""

    application_id: str
    module_id: str
    adapter_id: str
    executable: Path
    arguments: tuple[str, ...]
    working_directory: Path
    environment: Mapping[str, str]
    log_path: Path
    port: int | None
    health_target: HealthTarget
    shutdown_timeout_seconds: float


@dataclass(frozen=True)
class ProcessIdentity:
    """Durable process ownership and start ticks identity."""

    pid: int
    process_start_ticks: int
    expected_command_digest: str


@dataclass(frozen=True)
class ProcessStatus:
    """Durable process state, ownership identity, port, and health status."""

    state: Literal["starting", "running", "stopped", "failed"]
    identity: ProcessIdentity | None
    port: int | None
    health: str
    startup_duration_ms: float | None


@dataclass(frozen=True)
class ProcessResourceSnapshot:
    """Process resource observation snapshots (separated from expectations)."""

    current_memory_bytes: int | None
    peak_memory_bytes: int | None
    recent_cpu_percent: float | None
