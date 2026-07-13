"""Unit tests for path traversal, absolute IDs, and symlink security boundaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_workspace.errors import ManagedPathIsSymlink, PathEscapesWorkspace
from servicefabric_workspace.filesystem import check_managed_path_symlink, ensure_descendant


class TestPathSafety(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ensure_descendant_success(self) -> None:
        candidate = self.root / "applications/research-notes"
        # Since it is nested, it must resolve successfully
        resolved = ensure_descendant(self.root, candidate)
        self.assertEqual(resolved, candidate.resolve(strict=False))

    def test_ensure_descendant_escapes(self) -> None:
        candidate = self.root / "../escaped-directory"
        # Escaping candidates must raise PathEscapesWorkspace
        with self.assertRaises(PathEscapesWorkspace):
            ensure_descendant(self.root, candidate)

    def test_symlink_rejection(self) -> None:
        target = self.root / "target"
        target.mkdir()
        
        link = self.root / "symlinked-path"
        link.symlink_to(target)

        # Managed symlinks must raise ManagedPathIsSymlink
        with self.assertRaises(ManagedPathIsSymlink):
            check_managed_path_symlink(link)

        # Ordinary directories must pass safely
        check_managed_path_symlink(target)


if __name__ == "__main__":
    unittest.main()
