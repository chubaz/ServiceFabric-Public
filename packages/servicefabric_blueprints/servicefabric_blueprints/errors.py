"""Blueprint catalog errors."""

from __future__ import annotations


class BlueprintError(Exception):
    """Base error for reviewed blueprint operations."""


class DuplicateBlueprintRegistration(BlueprintError):
    """Raised when a blueprint ID and version are registered twice."""


class BlueprintNotFound(BlueprintError):
    """Raised when a blueprint cannot be resolved from the catalog."""
