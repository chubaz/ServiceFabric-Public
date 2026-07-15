"""Errors returned before a transport adapter performs a request."""

from __future__ import annotations


class CapabilityInvocationError(RuntimeError):
    """Base class for canonical capability-invocation failures."""


class CapabilityUnavailableError(CapabilityInvocationError):
    """Raised when a registered capability has no live endpoint."""


class OperationResolutionError(CapabilityInvocationError):
    """Raised when a capability's reviewed operation cannot be resolved."""


class BindingResolutionError(CapabilityInvocationError):
    """Raised when the requested reviewed HTTP binding cannot be resolved."""


class SchemaResolutionError(CapabilityInvocationError):
    """Raised when a reviewed schema reference cannot be resolved."""


class SchemaValidationError(CapabilityInvocationError):
    """Raised when invocation input or transport output violates its schema."""
