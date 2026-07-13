"""Unit/integration tests for atomic transaction rollbacks and failure recovery."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from servicefabric_workspace import ApplicationCreateRequest, resolve_workspace, WorkspaceService


class TestFailureRecovery(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_failed_creation_rolls_back_cleanly(self) -> None:
        context = resolve_workspace(explicit_workspace=self.root)
        service = WorkspaceService(context)
        service.initialize()

        req = ApplicationCreateRequest(
            application_id="research-notes", display_name="Research Notes"
        )

        # Inject a simulated failure during the file-writing (scaffolding) phase
        with patch(
            "servicefabric_workspace.scaffolding.scaffold_application",
            side_effect=RuntimeError("scaffolding simulated failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "scaffolding simulated failure"):
                service.create_application(req)

        # Verify that the target folder does NOT exist on disk and is completely rolled back
        self.assertFalse((self.root / "applications/research-notes").exists())

        # Verify that NO record of the application was written to the local registry
        apps = service.list_applications()
        self.assertEqual(len(apps), 0)


if __name__ == "__main__":
    unittest.main()
