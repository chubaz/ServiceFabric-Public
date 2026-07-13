"""Unit/integration tests for workspace initialization and repair."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_workspace import resolve_workspace, WorkspaceService
from servicefabric_workspace.errors import InvalidWorkspaceConfiguration


class TestInitialization(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_complete_initialization(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)
        
        status = service.initialize()
        self.assertTrue(status.initialized)
        self.assertTrue(status.created)
        self.assertEqual(len(status.repaired_directories), 0)

        # Verify workspace directory structures are created
        self.assertTrue((self.root / "applications").is_dir())
        self.assertTrue((self.root / "recipes").is_dir())
        self.assertTrue((self.root / "libraries").is_dir())
        self.assertTrue((self.root / ".servicefabric").is_dir())
        self.assertTrue((self.root / "workspace.yaml").is_file())
        self.assertTrue((self.root / ".servicefabric/registry/workspace.json").is_file())

    def test_idempotent_initialization(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)

        # Initial run
        status1 = service.initialize()
        self.assertTrue(status1.created)

        # Repeated run must be side-effect free and not overwrite workspace.yaml
        status2 = service.initialize()
        self.assertTrue(status2.initialized)
        self.assertFalse(status2.created)
        self.assertEqual(len(status2.repaired_directories), 0)

    def test_repair_missing_directories(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)
        
        service.initialize()

        # Delete an empty required directory to trigger repair
        target_dir = self.root / "recipes"
        target_dir.rmdir()
        self.assertFalse(target_dir.is_dir())

        # Idempotent initialize must repair the missing directory
        status = service.initialize()
        self.assertTrue(status.initialized)
        self.assertFalse(status.created)
        self.assertIn("recipes", status.repaired_directories)
        self.assertTrue(target_dir.is_dir())

    def test_refuse_malformed_metadata(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)

        # Write pre-existing malformed workspace.yaml
        yaml_file = self.root / "workspace.yaml"
        yaml_file.mkdir(parents=True, exist_ok=True)  # make it a directory to trigger parse error
        
        with self.assertRaises(InvalidWorkspaceConfiguration):
            service.initialize()


if __name__ == "__main__":
    unittest.main()
