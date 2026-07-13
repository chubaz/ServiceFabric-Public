"""Filesystem and path security utilities."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from servicefabric_workspace.errors import ManagedPathIsSymlink, PathEscapesWorkspace


def ensure_descendant(root: Path, candidate: Path) -> Path:
    """Enforces that a candidate path resides strictly within a resolved root directory.

    Args:
        root: The allowed root directory.
        candidate: The path to check.

    Returns:
        The resolved candidate path.

    Raises:
        PathEscapesWorkspace: If candidate escapes the root boundary.
    """
    resolved_root = root.resolve()
    # Resolve the candidate path (using strict=False since path may not exist yet)
    resolved_candidate = candidate.resolve(strict=False)

    # Note: is_relative_to is only in Python 3.9+, but we are guaranteed python 3.11+
    if not resolved_candidate.is_relative_to(resolved_root):
        raise PathEscapesWorkspace(
            f"Path security violation: resolved path '{resolved_candidate}' "
            f"escapes the allowed boundary of root '{resolved_root}'"
        )

    return resolved_candidate


def check_managed_path_symlink(path: Path) -> None:
    """Rejects symbolic links for platform-managed and workspace directories/files.

    Raises:
        ManagedPathIsSymlink: If the path exists and is a symbolic link.
    """
    if path.is_symlink():
        raise ManagedPathIsSymlink(
            f"Security boundary violation: managed path '{path}' cannot be a symbolic link."
        )


def atomic_write_text(path: Path, content: str) -> None:
    """Atomically writes text to a file using a temporary file in the same directory.

    Ensures that failures do not leave a partially written file or corrupt state.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temporary file in the target directory to ensure same-filesystem move (atomic replace)
    fd, temp_path_str = tempfile.mkstemp(dir=path.parent, prefix=".sf-atomic-")
    temp_path = Path(temp_path_str)
    
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            # Force write to disk
            os.fsync(handle.fileno())
        
        # Atomic rename
        os.replace(temp_path, path)
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise
