"""Errors raised by local resource binding resolution."""

from __future__ import annotations


class ResourceBindingError(RuntimeError):
    """Base error for local resource binding failures."""


class InvalidResourceBinding(ResourceBindingError, ValueError):
    """A local resource binding definition is invalid or unsafe."""


class DuplicateResourceBinding(ResourceBindingError):
    """A provider received duplicate resource binding definitions."""


class ResourceBindingNotFound(ResourceBindingError):
    """No local resource binding can satisfy a request."""


class ResourceBindingTypeMismatch(ResourceBindingError):
    """A local binding exists but does not match the requested contract."""
