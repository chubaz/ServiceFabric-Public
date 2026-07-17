"""A pure Gemini CLI adapter; subprocess ownership remains in the runtime."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from servicefabric_agent_provider_contracts import (
    ProviderEvent,
    ProviderExecutionRequest,
    ProviderExecutionResult,
    ProviderRunHandle,
    ProviderUsage,
)
from servicefabric_agentic_contracts import AgentTaskResult


_EVENT_TYPES = frozenset({"init", "message", "tool_use", "tool_result", "usage", "result", "warning", "error"})
_TASK_STATUSES = frozenset({"pending", "running", "success", "failed", "blocked", "cancelled"})


class GeminiCliAdapter:
    """Translate shared provider contracts to and from Gemini CLI data."""

    @property
    def provider_id(self) -> str:
        return "gemini"

    def probe(self) -> dict[str, Any]:
        """Describe this projection without inspecting or launching the provider."""
        return {
            "provider_id": self.provider_id,
            "executable": "gemini",
            "execution_owned_by": "provider-runtime",
        }

    def build_argv(self, request: ProviderExecutionRequest) -> tuple[str, ...]:
        """Build the deterministic non-interactive CLI invocation."""
        argv = [
            "gemini",
            "--output-format",
            "stream-json",
            "--approval-mode",
            "yolo",
            "--prompt",
            request.prompt,
        ]
        if request.model is not None:
            argv.extend(("--model", request.model))
        return tuple(argv)

    def parse_event(self, raw_event: str, sequence: int) -> ProviderEvent | None:
        """Convert one JSON-lines event to the shared event contract."""
        if sequence < 0:
            return None
        try:
            decoded = json.loads(raw_event)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(decoded, dict):
            return None

        event_type = decoded.get("type")
        if event_type not in _EVENT_TYPES:
            return None

        timestamp = self._timestamp(decoded.get("timestamp"))
        payload = {key: value for key, value in decoded.items() if key not in {"type", "timestamp"}}
        return ProviderEvent(
            sequence=sequence,
            event_type=event_type,
            timestamp=timestamp,
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
        """Recover a canonical result from collected events and process outcome."""
        status = self._result_status(events, exit_code)
        task_result = None
        if status in _TASK_STATUSES:
            task_result = AgentTaskResult(task_id=handle.task_id, status=status)
        return ProviderExecutionResult(
            handle=handle,
            status=status,
            task_result=task_result,
            usage=usage,
        )

    @staticmethod
    def _timestamp(value: object) -> datetime:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now(UTC)

    @staticmethod
    def _result_status(events: tuple[ProviderEvent, ...], exit_code: int | None) -> str:
        for event in reversed(events):
            if event.event_type != "result":
                continue
            status = event.payload.get("status")
            if status in {"success", "failed", "blocked", "cancelled"}:
                return status
        if exit_code is None:
            return "unknown"
        return "success" if exit_code == 0 else "failed"
