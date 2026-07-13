"""Crash-safe single-use approval binding consumption for local development."""

from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from pathlib import Path


class ApprovalAlreadyConsumedError(RuntimeError):
    """Raised when a single-use approval binding was previously consumed."""


class ApprovalConsumptionRepository:
    """Stores opaque binding identifiers only; approval content stays canonical audit data."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve(strict=False)
        if root.exists() and root.is_symlink():
            raise ApprovalAlreadyConsumedError("approval consumption root cannot be a symlink")
        self._root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, binding_id: str) -> Path:
        if not binding_id or len(binding_id) > 128:
            raise ApprovalAlreadyConsumedError("invalid approval binding identifier")
        return self._root / (hashlib.sha256(binding_id.encode("utf-8")).hexdigest() + ".consumed")

    def consumed(self) -> tuple[str, ...]:
        values: list[str] = []
        for path in sorted(self._root.glob("*.consumed")):
            try:
                value = path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise ApprovalAlreadyConsumedError("approval consumption record is unreadable") from exc
            if not value:
                raise ApprovalAlreadyConsumedError("approval consumption record is corrupt")
            values.append(value)
        return tuple(values)

    def consume(self, binding_id: str) -> None:
        path = self._path(binding_id)
        with self._lock:
            if path.exists():
                raise ApprovalAlreadyConsumedError("single-use approval binding was already consumed")
            fd, temporary_name = tempfile.mkstemp(prefix=".pending-", dir=self._root)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(binding_id + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                if path.exists():
                    raise ApprovalAlreadyConsumedError("single-use approval binding was already consumed")
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
