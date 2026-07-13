"""Defines provided and required module interfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProvidedInterface:
    id: str
    type: str  # e.g., 'http', 'python-package'
    protocol: str | None = None
    contract: str | None = None


@dataclass(frozen=True)
class RequiredInterface:
    id: str
