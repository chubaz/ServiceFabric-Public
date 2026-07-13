"""Unit/integration tests for the file-backed local application registry."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_workspace import ApplicationCreateRequest, resolve_workspace, WorkspaceService
from servicefabric_workspace.errors import ApplicationNotFound


class TestRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registry_operations(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)
        service.initialize()

        # Listing must be empty initially
        self.assertEqual(len(service.list_applications()), 0)

        # Register first application
        req1 = ApplicationCreateRequest(
            application_id="research-notes", display_name="Research Notes"
        )
        service.create_application(req1)

        # Register second application
        req2 = ApplicationCreateRequest(
            application_id="financial-analytics", display_name="Financial Analytics"
        )
        service.create_application(req2)

        # Listing must return registered records alphabetically sorted
        apps = service.list_applications()
        self.assertEqual(len(apps), 2)
        self.assertEqual(apps[0].application_id, "financial-analytics")
        self.assertEqual(apps[0].display_name, "Financial Analytics")
        self.assertEqual(apps[1].application_id, "research-notes")
        self.assertEqual(apps[1].display_name, "Research Notes")

        # Locate application layout
        layout = service.locate_application("research-notes")
        self.assertEqual(layout.application_id, "research-notes")
        self.assertTrue(layout.root.is_dir())

        # Locating an unregistered application ID must fail
        with self.assertRaises(ApplicationNotFound):
            service.locate_application("unknown-app")


if __name__ == "__main__":
    unittest.main()
