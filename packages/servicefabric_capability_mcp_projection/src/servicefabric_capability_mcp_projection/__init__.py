"""Thin MCP projection over registered application capabilities."""

from .projection import (
    CapabilityMcpCandidate,
    CapabilityMcpProjection,
    CapabilityMcpToolNotFoundError,
)

__all__ = [
    "CapabilityMcpCandidate",
    "CapabilityMcpProjection",
    "CapabilityMcpToolNotFoundError",
]
