from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class ApplicationContextPack:
    repository: str
    application_id: str | None
    files: tuple[str, ...]
    capability_ids: tuple[str, ...]

def build_context_pack(repository: str | Path, application_id: str | None = None, capability_ids: tuple[str, ...] = ()) -> ApplicationContextPack:
    root = Path(repository).resolve()
    candidates = ("AGENTS.md", "workspace.yaml", "README.md", "docs/architecture/specification-map.md")
    files = tuple(name for name in candidates if (root / name).is_file())
    return ApplicationContextPack(str(root), application_id, files, tuple(sorted(set(capability_ids))))
