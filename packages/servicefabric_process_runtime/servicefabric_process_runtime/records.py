"""Durable, file-backed module runtime record stores."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from servicefabric_workspace import WorkspaceLayout
from servicefabric_workspace.filesystem import atomic_write_text


@dataclass
class ModuleRuntimeRecord:
    """Represents a live or recently terminated module's runtime state."""

    application_id: str
    module_id: str
    adapter_id: str
    state: Literal["starting", "running", "stopped", "failed"]
    pid: int | None = None
    process_start_ticks: int | None = None
    port: int | None = None
    health: str = "unavailable"
    restart_count: int = 0
    startup_duration_ms: float | None = None
    peak_memory_bytes: int | None = None


class ModuleRuntimeStore:
    """Handles thread-safe locking and atomic saving/loading of runtime records."""

    def __init__(self, workspace: WorkspaceLayout):
        self.workspace = workspace

    def get_lock_path(self, application_id: str, module_id: str) -> Path:
        """Returns the specific file lock path for a given module."""
        return self.workspace.locks / f"module-{application_id}-{module_id}.lock"

    def get_record_path(self, application_id: str, module_id: str) -> Path:
        """Returns the storage path for the module's JSON record."""
        return self.workspace.instances / application_id / f"{module_id}.json"

    def save(self, record: ModuleRuntimeRecord) -> None:
        """Atomically saves the module runtime record to the filesystem."""
        path = self.get_record_path(record.application_id, record.module_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = asdict(record)
        data["format"] = 1
        
        atomic_write_text(path, json.dumps(data, indent=2) + "\n")

    def load(self, application_id: str, module_id: str) -> ModuleRuntimeRecord | None:
        """Loads and parses the module runtime record if it exists on disk."""
        path = self.get_record_path(application_id, module_id)
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                return ModuleRuntimeRecord(
                    application_id=data["application_id"],
                    module_id=data["module_id"],
                    adapter_id=data["adapter_id"],
                    state=data["state"],
                    pid=data.get("pid"),
                    process_start_ticks=data.get("process_start_ticks"),
                    port=data.get("port"),
                    health=data.get("health", "unavailable"),
                    restart_count=data.get("restart_count", 0),
                    startup_duration_ms=data.get("startup_duration_ms"),
                    peak_memory_bytes=data.get("peak_memory_bytes"),
                )
        except Exception:
            return None
