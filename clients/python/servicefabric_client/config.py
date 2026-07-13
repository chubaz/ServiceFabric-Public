"""Minimal explicit connection configuration for remote consumers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceFabricConnection:
    endpoint: str
    toolset: str = "research-demo"

    @classmethod
    def load(cls, path: Path | str) -> "ServiceFabricConnection":
        values = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"')
        endpoint = values.get("endpoint")
        if endpoint is None:
            raise ValueError("connection configuration requires endpoint")
        return cls(endpoint=endpoint, toolset=values.get("toolset", "research-demo"))
