"""Loopback REST projection for the integration capability consumer facade."""

from .gateway import CapabilityConsumerBoundary, CapabilityRestGateway
from .server import LoopbackCapabilityRestServer

__all__ = [
    "CapabilityRestGateway",
    "CapabilityConsumerBoundary",
    "LoopbackCapabilityRestServer",
]
