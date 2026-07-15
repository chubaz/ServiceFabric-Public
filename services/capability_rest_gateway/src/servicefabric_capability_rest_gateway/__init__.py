"""Loopback REST projection for the canonical capability runtime boundary."""

from .gateway import CapabilityRestGateway, CapabilityRuntimeBoundary
from .server import LoopbackCapabilityRestServer

__all__ = [
    "CapabilityRestGateway",
    "CapabilityRuntimeBoundary",
    "LoopbackCapabilityRestServer",
]
