"""Pi CLI translation adapter; process lifecycle remains runtime-owned."""
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


class PiHarnessAdapter:
    """Translate Pi's print-mode JSON stream into provider contracts."""

    @property
    def provider_id(self) -> str:
        return "pi"

    def probe(self) -> dict[str, Any]:
        """Describe the executable without invoking it."""
        return {"provider_id": self.provider_id, "executable": "pi", "protocol": "json"}

    def build_argv(self, request: ProviderExecutionRequest) -> tuple[str, ...]:
        """Build a safe argv vector; the shared runtime performs execution."""
        if request.provider_id != self.provider_id:
            raise ValueError("PiHarnessAdapter only accepts provider_id 'pi'")

        argv: list[str] = ["pi", "--print", "--output-format", "json"]
        if request.model is not None:
            argv.extend(("--model", request.model))
        if request.maximum_turns is not None:
            argv.extend(("--max-turns", str(request.maximum_turns)))
        argv.append(request.prompt)
        return tuple(argv)

    def parse_event(self, raw_event: str, sequence: int) -> ProviderEvent | None:
        """Convert one JSON-lines record, ignoring blank and unknown records."""
        if not raw_event.strip():
            return None
        try:
            record = json.loads(raw_event)
        except json.JSONDecodeError:
            return ProviderEvent(
                sequence=sequence,
                event_type="warning",
                timestamp=datetime.now(timezone.utc),
                payload={"message": "Pi emitted a non-JSON record"},
            )
        if not isinstance(record, dict):
            return None

        event_type = self._event_type(record)
        if event_type is None:
            return None
        return ProviderEvent(
            sequence=sequence,
            event_type=event_type,
            timestamp=self._timestamp(record),
            payload=record,
        )

    def recover_result(
        self,
        handle: ProviderRunHandle,
        events: tuple[ProviderEvent, ...],
        usage: ProviderUsage,
        *,
        exit_code: int | None,
    ) -> ProviderExecutionResult:
        """Represent process outcome using only shared provider contracts."""
        status = "success" if exit_code == 0 else "unknown" if exit_code is None else "failed"
        result_handle = handle.model_copy(update={"state": status})
        return ProviderExecutionResult(handle=result_handle, status=status, usage=usage)

    @staticmethod
    def _event_type(record: dict[str, Any]) -> str | None:
        source_type = record.get("type") or record.get("event")
        if not isinstance(source_type, str):
            return None
        return {
            "init": "init",
            "message": "message",
            "assistant": "message",
            "tool_use": "tool_use",
            "tool_call": "tool_use",
            "tool_result": "tool_result",
            "usage": "usage",
            "result": "result",
            "error": "error",
            "warning": "warning",
        }.get(source_type)

    @staticmethod
    def _timestamp(record: dict[str, Any]) -> datetime:
        value = record.get("timestamp")
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now(timezone.utc)
