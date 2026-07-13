"""Integration tests for workspace isolation boundaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_workspace import ApplicationCreateRequest, resolve_workspace, WorkspaceService


class TestWorkspaceIsolation(unittest.TestCase):
    def test_workspaces_are_fully_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as dir_a, tempfile.TemporaryDirectory() as dir_b:
            root_a = Path(dir_a)
            root_b = Path(dir_b)

            # Resolve and initialize Workspace A
            context_a = resolve_workspace(explicit_workspace=root_a)
            service_a = WorkspaceService(context_a)
            service_a.initialize()

            # Resolve and initialize Workspace B
            context_b = resolve_workspace(explicit_workspace=root_b)
            service_b = WorkspaceService(context_b)
            service_b.initialize()

            # Create same application ID 'research-notes' in workspace A
            req_a = ApplicationCreateRequest(
                application_id="research-notes", display_name="Research Notes A"
            )
            service_a.create_application(req_a)

            # Create same application ID 'research-notes' in workspace B
            req_b = ApplicationCreateRequest(
                application_id="research-notes", display_name="Research Notes B"
            )
            service_b.create_application(req_b)

            # Verify registry records are completely separate and contain their specific display names
            apps_a = service_a.list_applications()
            apps_b = service_b.list_applications()

            self.assertEqual(len(apps_a), 1)
            self.assertEqual(apps_a[0].display_name, "Research Notes A")

            self.assertEqual(len(apps_b), 1)
            self.assertEqual(apps_b[0].display_name, "Research Notes B")

            # Check that file system paths do not overlap or leak into each other
            path_a = (root_a / "applications/research-notes").resolve()
            path_b = (root_b / "applications/research-notes").resolve()

            self.assertTrue(path_a.is_dir())
            self.assertTrue(path_b.is_dir())
            self.assertNotEqual(path_a, path_b)


if __name__ == "__main__":
    unittest.main()
