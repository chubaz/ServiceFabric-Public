"""Errors raised while composing generated developer guidance."""

from __future__ import annotations


class GuidanceError(ValueError):
    """Base error for invalid guidance input or output."""


class InvalidGuidancePath(GuidanceError):
    """Raised when a guidance path could escape the generated workspace."""


class DuplicateGuidancePath(GuidanceError):
    """Raised when two fragments would write the same generated file."""


class UnknownGuidanceKit(GuidanceError):
    """Raised when no reviewed guidance exists for a requested kit."""
