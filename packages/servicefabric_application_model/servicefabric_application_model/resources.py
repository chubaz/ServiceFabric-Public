"""Defines module resource requests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceRequest:
    id: str
    type: str  # e.g., 'relational-database', 'message-queue', 'object-storage'
    scope: str = "application"
