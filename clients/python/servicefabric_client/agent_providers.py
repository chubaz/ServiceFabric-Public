"""Integration composition for provider adapters; adapters remain independently owned."""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from servicefabric_agent_provider_contracts import ExecutableHarnessAdapter, ProviderPolicy


KNOWN_PROVIDER_IDS = ("claude", "codex", "gemini", "pi")


class ProviderRegistry:
    """Explicit adapter registry that never imports optional providers dynamically."""

    def __init__(self, adapters: Iterable[ExecutableHarnessAdapter] = ()) -> None:
        values = tuple(adapters)
        identifiers = tuple(adapter.provider_id for adapter in values)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("provider adapter IDs must be unique")
        self._adapters = {adapter.provider_id: adapter for adapter in values}

    def get(self, provider_id: str) -> ExecutableHarnessAdapter:
        try:
            return self._adapters[provider_id]
        except KeyError as error:
            raise ValueError(f"provider adapter is unavailable: {provider_id}") from error

    def list(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {"provider_id": provider_id, "available": provider_id in self._adapters}
            for provider_id in KNOWN_PROVIDER_IDS
        )

    def doctor(self, provider_id: str | None = None) -> tuple[dict[str, object], ...]:
        targets = (provider_id,) if provider_id else KNOWN_PROVIDER_IDS
        result: list[dict[str, object]] = []
        for identifier in targets:
            adapter = self._adapters.get(identifier)
            if adapter is None:
                result.append({"provider_id": identifier, "available": False, "probe": None})
            else:
                result.append({"provider_id": identifier, "available": True, "probe": adapter.probe()})
        return tuple(result)


def load_provider_policy(path: str | Path) -> ProviderPolicy:
    """Load a local JSON policy; credentials are deliberately not part of its schema."""
    try:
        raw: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("provider policy must be a valid JSON file") from error
    return ProviderPolicy.model_validate(raw)
