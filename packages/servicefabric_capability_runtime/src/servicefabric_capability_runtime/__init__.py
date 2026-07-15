"""Runtime capability availability derived from owning-module health."""

from .models import (
    CapabilityAvailability,
    CapabilityAvailabilityReason,
    CapabilityAvailabilityState,
    CapabilityRuntimeTarget,
    ModuleHealth,
)
from .runtime import CapabilityAvailabilityResolver, ModuleHealthSource
from .serialization import serialize_availability_snapshot

__all__ = [
    "CapabilityAvailability",
    "CapabilityAvailabilityReason",
    "CapabilityAvailabilityResolver",
    "CapabilityAvailabilityState",
    "CapabilityRuntimeTarget",
    "ModuleHealth",
    "ModuleHealthSource",
    "serialize_availability_snapshot",
]
