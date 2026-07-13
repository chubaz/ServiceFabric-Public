"""File locking utilities for ServiceFabric mutations."""

from __future__ import annotations

import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    """Acquires an exclusive file lock on the specified path.

    Creates any missing parent directories automatically.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
