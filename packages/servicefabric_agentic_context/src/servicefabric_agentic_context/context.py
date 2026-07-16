from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_CONTEXT_FILE_CANDIDATES = (
    "AGENTS.md",
    "workspace.yaml",
    "README.md",
    "docs/architecture/specification-map.md",
)
_MAX_CAPABILITY_IDS = 64


@dataclass(frozen=True, slots=True)
class ApplicationContextPack:
    """Deterministic references to a repository's bounded context."""

    repository: str
    application_id: str | None
    files: tuple[str, ...]
    capability_ids: tuple[str, ...]


def build_context_pack(
    repository: str | Path,
    application_id: str | None = None,
    capability_ids: Iterable[str] = (),
) -> ApplicationContextPack:
    """Build a stable context pack without scanning the repository."""

    root = Path(repository).resolve()
    if not root.exists():
        raise FileNotFoundError(f"repository does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"repository is not a directory: {root}")

    files = tuple(
        relative_path
        for relative_path in _CONTEXT_FILE_CANDIDATES
        if _is_repository_file(root, relative_path)
    )
    normalized_capability_ids = tuple(sorted(set(capability_ids)))
    if len(normalized_capability_ids) > _MAX_CAPABILITY_IDS:
        raise ValueError(
            f"capability_ids contains more than {_MAX_CAPABILITY_IDS} unique values"
        )

    return ApplicationContextPack(
        repository=str(root),
        application_id=application_id,
        files=files,
        capability_ids=normalized_capability_ids,
    )


def _is_repository_file(root: Path, relative_path: str) -> bool:
    candidate = root / relative_path
    return candidate.is_file() and candidate.resolve().is_relative_to(root)
