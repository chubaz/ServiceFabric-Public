"""Translate canonical provider requests to and from Claude Code's JSON stream."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from servicefabric_agent_provider_contracts import (
    ProviderEvent,
    ProviderExecutionRequest,
    ProviderExecutionResult,
    ProviderRunHandle,
    ProviderUsage,
)


class ClaudeCodeAdapter:
    """A pure Claude Code CLI translation adapter.

    The provider runtime supplies the working directory, environment, process
    lifecycle, stream collection, and artifact persistence. This adapter only
    builds a deterministic argument vector and normalizes provider events.
    """

    _provider_id = "claude"

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def probe(self) -> dict[str, Any]:
        """Describe the executable without probing or launching a process."""
        return {
            "provider_id": self.provider_id,
            "executable": "claude",
            "execution_owned_by": "provider-runtime",
        }

    def build_argv(self, request: ProviderExecutionRequest) -> tuple[str, ...]:
        """Render the non-interactive Claude Code command for a request."""
        if request.provider_id != self.provider_id:
            raise ValueError("Claude Code adapter only accepts provider_id 'claude'")

        arguments = ["claude", "--print", "--output-format", "stream-json", "--verbose"]
        if request.model is not None:
            arguments.extend(("--model", request.model))
        if request.maximum_turns is not None:
            arguments.extend(("--max-turns", str(request.maximum_turns)))
        arguments.append(request.prompt)
        return tuple(arguments)

    def parse_event(self, raw_event: str, sequence: int) -> ProviderEvent | None:
        """Normalize one JSON-line event; malformed or unknown events are ignored."""
        try:
            payload = json.loads(raw_event)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        event_type = self._event_type(payload.get("type"))
        if event_type is None:
            return None
        return ProviderEvent(
            sequence=sequence,
            event_type=event_type,
            timestamp=self._timestamp(payload.get("timestamp")),
            payload=payload,
        )

    def recover_result(
        self,
        handle: ProviderRunHandle,
        events: tuple[ProviderEvent, ...],
        usage: ProviderUsage,
        *,
        exit_code: int | None,
    ) -> ProviderExecutionResult:
        """Recover a canonical terminal state without deriving task side effects."""
        status = self._status(events, exit_code)
        return ProviderExecutionResult(handle=handle, status=status, usage=usage)

    @staticmethod
    def _event_type(raw_type: object) -> str | None:
        return {
            "system": "init",
            "assistant": "message",
            "user": "tool_result",
            "tool_use": "tool_use",
            "tool_result": "tool_result",
            "usage": "usage",
            "result": "result",
            "warning": "warning",
            "error": "error",
        }.get(raw_type)

    @staticmethod
    def _timestamp(value: object) -> datetime:
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
            else:
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc)

    @staticmethod
    def _status(events: tuple[ProviderEvent, ...], exit_code: int | None) -> str:
        if exit_code is not None and exit_code != 0:
            return "failed"
        if any(event.event_type == "error" for event in events):
            return "failed"
        results = tuple(event for event in events if event.event_type == "result")
        if results:
            final = results[-1].payload
            return "failed" if final.get("is_error") else "success"
        return "unknown"
