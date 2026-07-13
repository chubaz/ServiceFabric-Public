"""System-level and CLI-driven acceptance tests for ServiceFabric Workspaces."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VENV_BIN = Path("/home/lorenzoccasoni/.virtualenvs/servicefabric/bin")


class CliWorkspaceJourneysTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(
        self,
        *arguments: str,
        workspace: Path | None = None,
        home: Path | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        # Construct isolated environment, prepending the virtual environment bin
        environment = os.environ.copy()
        path_env = str(VENV_BIN) + os.pathsep + environment.get("PATH", "")
        environment["PATH"] = path_env
        
        # Clear existing variables to prevent pollution
        environment.pop("SERVICEFABRIC_WORKSPACE", None)
        environment.pop("SERVICEFABRIC_HOME", None)

        if workspace is not None:
            environment["SERVICEFABRIC_WORKSPACE"] = str(workspace)
        if home is not None:
            environment["SERVICEFABRIC_HOME"] = str(home)

        command = ["servicefabric", *arguments]
        
        return subprocess.run(
            command,
            cwd=cwd or ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )

    def test_cli_workspace_lifecycle_journey(self) -> None:
        ws_dir = self.temp_path / "workspace"

        # 1. Initialize full development workspace
        res_init = self.run_cli("workspace", "init", str(ws_dir))
        self.assertEqual(res_init.returncode, 0)
        self.assertIn("Created ServiceFabric development workspace", res_init.stdout)
        self.assertIn(str(ws_dir), res_init.stdout)

        # 2. Workspace status
        res_status = self.run_cli("workspace", "status", workspace=ws_dir)
        self.assertEqual(res_status.returncode, 0)
        self.assertIn("ServiceFabric development workspace", res_status.stdout)
        self.assertIn("Applications: 0", res_status.stdout)
        self.assertIn("Validation:   valid", res_status.stdout)

        # Workspace status JSON output
        res_status_json = self.run_cli("workspace", "status", "--json", workspace=ws_dir)
        self.assertEqual(res_status_json.returncode, 0)
        status_data = json.loads(res_status_json.stdout)
        self.assertEqual(status_data["applications"], 0)
        self.assertEqual(status_data["validation"], "valid")

        # 3. Workspace paths
        res_paths = self.run_cli("workspace", "paths", workspace=ws_dir)
        self.assertEqual(res_paths.returncode, 0)
        self.assertIn("Workspace paths", res_paths.stdout)
        self.assertIn(str(ws_dir / "applications"), res_paths.stdout)

        # Workspace paths JSON output
        res_paths_json = self.run_cli("workspace", "paths", "--json", workspace=ws_dir)
        self.assertEqual(res_paths_json.returncode, 0)
        paths_data = json.loads(res_paths_json.stdout)
        self.assertEqual(paths_data["applications"], str(ws_dir / "applications"))

        # 4. Workspace validate
        res_val = self.run_cli("workspace", "validate", workspace=ws_dir)
        self.assertEqual(res_val.returncode, 0)
        self.assertIn("Workspace validation passed", res_val.stdout)

        res_val_deep = self.run_cli("workspace", "validate", "--deep", workspace=ws_dir)
        self.assertEqual(res_val_deep.returncode, 0)
        self.assertIn("Workspace validation passed", res_val_deep.stdout)

    def test_cli_application_source_journey(self) -> None:
        ws_dir = self.temp_path / "workspace"
        self.run_cli("workspace", "init", str(ws_dir))

        # 1. Create empty application
        res_create = self.run_cli(
            "apps",
            "create",
            "research-notes",
            "--name",
            "Research Notes App",
            "--empty",
            workspace=ws_dir,
        )
        self.assertEqual(res_create.returncode, 0)
        self.assertIn("Created application source: research-notes", res_create.stdout)
        self.assertIn("Location: applications/research-notes", res_create.stdout)

        # Verify filesystem structures exist
        self.assertTrue((ws_dir / "applications/research-notes/AGENTS.md").is_file())
        self.assertTrue((ws_dir / "applications/research-notes/.servicefabric/application.yaml").is_file())

        # 2. Locate application
        res_locate = self.run_cli("apps", "locate", "research-notes", workspace=ws_dir)
        self.assertEqual(res_locate.returncode, 0)
        self.assertEqual(res_locate.stdout.strip(), str((ws_dir / "applications/research-notes").resolve()))

        # 3. Inspect application
        res_inspect = self.run_cli("apps", "inspect", "research-notes", workspace=ws_dir)
        self.assertEqual(res_inspect.returncode, 0)
        self.assertIn("Research Notes App", res_inspect.stdout)
        self.assertIn("ID:          research-notes", res_inspect.stdout)
        self.assertIn("Installed:   no", res_inspect.stdout)
        self.assertIn("Running:     no", res_inspect.stdout)

        # 4. List applications
        res_list = self.run_cli("apps", "list", workspace=ws_dir)
        self.assertEqual(res_list.returncode, 0)
        self.assertIn("research-notes", res_list.stdout)
        self.assertIn("development source", res_list.stdout)

    def test_parent_discovery(self) -> None:
        ws_dir = self.temp_path / "workspace"
        self.run_cli("workspace", "init", str(ws_dir))
        self.run_cli(
            "apps",
            "create",
            "research-notes",
            "--name",
            "Research Notes",
            "--empty",
            workspace=ws_dir,
        )

        # Set cwd deeply nested inside the application modules directory
        nested_dir = ws_dir / "applications/research-notes/modules"
        nested_dir.mkdir(parents=True, exist_ok=True)

        # Run command from nested folder without explicitly providing workspace
        res_status = self.run_cli("workspace", "status", cwd=nested_dir)
        self.assertEqual(res_status.returncode, 0)
        self.assertIn("ServiceFabric development workspace", res_status.stdout)
        self.assertIn(str(ws_dir), res_status.stdout)

    def test_mode_boundary(self) -> None:
        # 1. Set only SERVICEFABRIC_HOME state-only mode
        state_dir = self.temp_path / "state-home"
        res_init = self.run_cli("init", home=state_dir)
        self.assertEqual(res_init.returncode, 0)
        self.assertIn("Created local workspace", res_init.stdout)

        # 2. Legacy commands must work fine in state-only mode
        res_list = self.run_cli("apps", "list", home=state_dir)
        self.assertEqual(res_list.returncode, 0)

        # 3. Source commands (like apps create) must fail safely with required-workspace warning
        res_create = self.run_cli(
            "apps",
            "create",
            "research-notes",
            "--name",
            "Research Notes",
            "--empty",
            home=state_dir,
        )
        self.assertNotEqual(res_create.returncode, 0)
        self.assertIn("A development workspace is required", res_create.stderr)
        self.assertIn("servicefabric workspace init", res_create.stderr)

        # Ensure no applications directory was created implicitly
        self.assertFalse((state_dir / "applications").exists())

    def test_workspace_isolation(self) -> None:
        ws_a = self.temp_path / "workspace-a"
        ws_b = self.temp_path / "workspace-b"

        self.run_cli("workspace", "init", str(ws_a))
        self.run_cli("workspace", "init", str(ws_b))

        # Create 'research-notes' in workspace A
        self.run_cli(
            "apps",
            "create",
            "research-notes",
            "--name",
            "Research A",
            "--empty",
            workspace=ws_a,
        )

        # Create 'research-notes' in workspace B
        self.run_cli(
            "apps",
            "create",
            "research-notes",
            "--name",
            "Research B",
            "--empty",
            workspace=ws_b,
        )

        # Verify isolation via status and inspections
        inspect_a = self.run_cli("apps", "inspect", "research-notes", workspace=ws_a)
        self.assertIn("Research A", inspect_a.stdout)
        self.assertNotIn("Research B", inspect_a.stdout)

        inspect_b = self.run_cli("apps", "inspect", "research-notes", workspace=ws_b)
        self.assertIn("Research B", inspect_b.stdout)
        self.assertNotIn("Research A", inspect_b.stdout)


if __name__ == "__main__":
    unittest.main()
