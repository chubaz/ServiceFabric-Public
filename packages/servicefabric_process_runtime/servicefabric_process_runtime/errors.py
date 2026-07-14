"""Domain exceptions for ServiceFabric Process Runtime."""

from __future__ import annotations


class ProcessRuntimeError(RuntimeError):
    """Base exception for all process runtime errors."""
    pass


class ProcessStartError(ProcessRuntimeError):
    """Raised when a subprocess fails to launch or report health before timeout."""
    pass


class StaleProcessError(ProcessRuntimeError):
    """Raised when process ownership checks detect a stale process identity mismatch."""
    pass


class PortAllocationError(ProcessRuntimeError):
    """Raised when dynamic loopback port allocation fails."""
    pass
