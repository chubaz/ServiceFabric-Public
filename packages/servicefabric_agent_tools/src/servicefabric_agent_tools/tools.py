"""Bounded, provider-neutral tools exposed to coding agents."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from servicefabric_agentic_contracts import AgentToolResult


class _CapabilityFacade(Protocol):
    """The narrow public capability surface required by this adapter."""

    def discover(self, application_id: str) -> object: ...


class BoundedAgentTools:
    """Expose an explicit allowlist of read-only agent operations.

    Workspace inspection is confined to ``repository`` after resolving symlinks.
    Capability discovery is delegated to an injected public facade; this adapter
    never reaches into a capability registry or runtime directly.
    """

    _WORKSPACE_INSPECT = "workspace.inspect"
    _CAPABILITIES_DISCOVER = "capabilities.discover"

    def __init__(
        self,
        repository: str | Path,
        capability_facade: _CapabilityFacade | None = None,
    ) -> None:
        self.root = Path(repository).resolve()
        self.facade = capability_facade

    def invoke(self, name: str, arguments: dict[str, Any]) -> AgentToolResult:
        """Invoke one allowlisted operation and return a structured result."""

        if not isinstance(arguments, Mapping):
            return _failed("tool arguments must be a mapping")
        if name == self._WORKSPACE_INSPECT:
            return self._inspect_workspace(arguments)
        if name == self._CAPABILITIES_DISCOVER:
            return self._discover_capabilities(arguments)
        return _blocked("tool is not allowlisted")

    def _inspect_workspace(self, arguments: Mapping[str, Any]) -> AgentToolResult:
        if set(arguments) - {"path"}:
            return _failed("workspace.inspect received unsupported arguments")

        relative = arguments.get("path", ".")
        if not isinstance(relative, str) or not relative:
            return _failed("workspace.inspect path must be a non-empty string")

        try:
            target = (self.root / relative).resolve()
        except (OSError, RuntimeError):
            return _failed("workspace path could not be resolved")

        if target != self.root and self.root not in target.parents:
            return _blocked("path escapes repository")

        return AgentToolResult(
            status="success",
            summary="workspace path inspected",
            data={"path": str(target), "exists": target.exists()},
        )

    def _discover_capabilities(
        self, arguments: Mapping[str, Any]
    ) -> AgentToolResult:
        if self.facade is None:
            return _blocked("capability discovery is unavailable")
        if set(arguments) != {"application_id"}:
            return _failed(
                "capabilities.discover requires only application_id"
            )

        application_id = arguments["application_id"]
        if not isinstance(application_id, str) or not application_id.strip():
            return _failed("application_id must be a non-empty string")

        try:
            capabilities = self.facade.discover(application_id)
        except Exception:  # The provider boundary must return a contract result.
            return _failed("capability discovery failed")

        return AgentToolResult(
            status="success",
            summary="capabilities discovered",
            data={"capabilities": capabilities},
        )


def _blocked(summary: str) -> AgentToolResult:
    return AgentToolResult(status="blocked", summary=summary)


def _failed(summary: str) -> AgentToolResult:
    return AgentToolResult(status="failed", summary=summary)
