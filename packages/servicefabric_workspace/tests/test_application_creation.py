"""Unit/integration tests for application scaffolding and creation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_workspace import ApplicationCreateRequest, resolve_workspace, WorkspaceService
from servicefabric_workspace.errors import ApplicationAlreadyExists, WorkspaceNotInitialized


class TestApplicationCreation(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_application_creation_success(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)
        service.initialize()

        req = ApplicationCreateRequest(
            application_id="research-notes", display_name="Research Notes"
        )
        record = service.create_application(req)
        
        self.assertEqual(record.application_id, "research-notes")
        self.assertEqual(record.display_name, "Research Notes")
        self.assertEqual(record.source_path, "applications/research-notes")
        self.assertEqual(record.status, "development")

        # Verify scaffolding files
        app_dir = self.root / "applications/research-notes"
        self.assertTrue(app_dir.is_dir())
        self.assertTrue((app_dir / "README.md").is_file())
        self.assertTrue((app_dir / "AGENTS.md").is_file())
        self.assertTrue((app_dir / "ARCHITECTURE.md").is_file())
        self.assertTrue((app_dir / "DEVELOPMENT.md").is_file())
        self.assertTrue((app_dir / "modules").is_dir())
        self.assertTrue((app_dir / "tests").is_dir())
        self.assertTrue((app_dir / ".servicefabric/application.yaml").is_file())
        self.assertTrue((app_dir / ".servicefabric/blueprint.yaml").is_file())
        self.assertTrue((app_dir / ".servicefabric/bindings.yaml").is_file())
        self.assertTrue((app_dir / ".servicefabric/development.yaml").is_file())

    def test_creation_fails_without_initialization(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)
        
        req = ApplicationCreateRequest(
            application_id="research-notes", display_name="Research Notes"
        )
        with self.assertRaises(WorkspaceNotInitialized):
            service.create_application(req)

    def test_creation_rejects_duplicate_application_ids(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)
        service.initialize()

        req = ApplicationCreateRequest(
            application_id="research-notes", display_name="Research Notes"
        )
        service.create_application(req)

        # Attempt to create duplicate ID must fail
        with self.assertRaises(ApplicationAlreadyExists):
            service.create_application(req)


if __name__ == "__main__":
    unittest.main()
