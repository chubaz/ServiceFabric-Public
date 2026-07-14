"""Defines module lifecycle, readiness, and shutdown configurations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReadinessProbe:
    type: str  # e.g., 'http', 'tcp', 'command'
    path: str | None = None
    port: int | None = None


@dataclass(frozen=True)
class ShutdownConfig:
    timeout_seconds: int = 10


@dataclass(frozen=True)
class LifecycleConfig:
    start_after: tuple[str, ...] = field(default_factory=tuple)
    readiness: ReadinessProbe | None = None
    shutdown: ShutdownConfig = field(default_factory=ShutdownConfig)
