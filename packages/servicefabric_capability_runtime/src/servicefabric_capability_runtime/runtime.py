"""Deterministic derivation of capability availability from module health."""

from __future__ import annotations

from typing import Protocol

from .models import (
    CapabilityAvailability,
    CapabilityAvailabilityReason,
    CapabilityAvailabilityState,
    CapabilityRuntimeTarget,
    ModuleHealth,
)


class ModuleHealthSource(Protocol):
    """Supplies bounded health observations for reviewed module identities."""

    def get_module_health(self, application_id: str, module_id: str) -> ModuleHealth | None:
        """Return the current health observation, or ``None`` when absent."""


class CapabilityAvailabilityResolver:
    """Derive availability without changing static capability definitions."""

    def __init__(self, module_health_source: ModuleHealthSource) -> None:
        self._module_health_source = module_health_source

    def resolve(self, target: CapabilityRuntimeTarget) -> CapabilityAvailability:
        """Return a deterministic availability result for ``target``.

        Only a ``running`` module with a ``healthy`` health observation is
        available.  All other lifecycle states remain registered but resolve
        to an explicit unavailable reason.
        """

        health = self._module_health_source.get_module_health(target.application_id, target.module_id)
        reason = self._reason_for(health)
        state = (
            CapabilityAvailabilityState.AVAILABLE
            if reason is CapabilityAvailabilityReason.MODULE_HEALTHY
            else CapabilityAvailabilityState.UNAVAILABLE
        )
        return CapabilityAvailability(
            capability_id=target.capability_id,
            application_id=target.application_id,
            module_id=target.module_id,
            state=state,
            reason=reason,
        )

    @staticmethod
    def _reason_for(health: ModuleHealth | None) -> CapabilityAvailabilityReason:
        if health is None:
            return CapabilityAvailabilityReason.MODULE_NOT_FOUND
        if health.state == "running":
            return (
                CapabilityAvailabilityReason.MODULE_HEALTHY
                if health.health == "healthy"
                else CapabilityAvailabilityReason.MODULE_UNHEALTHY
            )
        if health.state == "starting":
            return CapabilityAvailabilityReason.MODULE_STARTING
        if health.state == "stopped":
            return CapabilityAvailabilityReason.MODULE_STOPPED
        return CapabilityAvailabilityReason.MODULE_FAILED
