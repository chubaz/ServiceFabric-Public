"""Immutable records used to derive capability runtime availability."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class CapabilityAvailabilityState(StrEnum):
    """The runtime state exposed for a registered capability."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class CapabilityAvailabilityReason(StrEnum):
    """Stable, non-sensitive explanation for an availability result."""

    MODULE_HEALTHY = "module_healthy"
    MODULE_NOT_FOUND = "module_not_found"
    MODULE_STARTING = "module_starting"
    MODULE_STOPPED = "module_stopped"
    MODULE_FAILED = "module_failed"
    MODULE_UNHEALTHY = "module_unhealthy"


@dataclass(frozen=True)
class CapabilityRuntimeTarget:
    """The reviewed owner of one statically registered capability."""

    capability_id: str
    application_id: str
    module_id: str


@dataclass(frozen=True)
class ModuleHealth:
    """A bounded observation of one owning module's lifecycle and health."""

    application_id: str
    module_id: str
    state: Literal["starting", "running", "stopped", "failed"]
    health: str


@dataclass(frozen=True)
class CapabilityAvailability:
    """The derived availability state and reason for one capability target."""

    capability_id: str
    application_id: str
    module_id: str
    state: CapabilityAvailabilityState
    reason: CapabilityAvailabilityReason

    @property
    def available(self) -> bool:
        """Whether the capability may be invoked at this instant."""

        return self.state is CapabilityAvailabilityState.AVAILABLE

    def to_dict(self) -> dict[str, str]:
        """Return the stable JSON-ready representation of this derived view."""

        return {
            "capabilityId": self.capability_id,
            "applicationId": self.application_id,
            "moduleId": self.module_id,
            "state": self.state.value,
            "reason": self.reason.value,
        }
