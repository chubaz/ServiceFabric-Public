"""Executable acceptance specification for the Wave-3 integration journey.

This lane owns the stable, framework-spanning expectations.  The generator,
builder, and CLI lanes supply the implementation that the integration gate
executes against this specification.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from servicefabric_client.main import dispatch
from servicefabric_application_builder import ApplicationBuildCoordinator
from servicefabric_application_generator import materialize_blueprint
from servicefabric_blueprints import RESEARCH_NOTES_BLUEPRINT
from servicefabric_workspace import ApplicationAlreadyExists, resolve_workspace, WorkspaceService


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "wave_03" / "fresh_workspace_journey.json"


class FreshWorkspaceAcceptanceSpecificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specification = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_journey_is_the_required_fresh_workspace_lifecycle(self) -> None:
        self.assertEqual(
            [step["command"] for step in self.specification["journey"]],
            [
                "workspace init",
                "apps create",
                "apps modules",
                "apps validate",
                "dev prepare",
                "dev start",
                "dev status",
                "dev restart",
                "apps build",
                "dev stop",
            ],
        )

    def test_generation_covers_ordinary_supported_framework_source(self) -> None:
        modules = self.specification["application"]["modules"]
        self.assertEqual(
            [(module["id"], module["kit"]) for module in modules],
            [
                ("api", "fastapi-service"),
                ("web", "react-web"),
                ("domain", "python-library"),
            ],
        )
        for module in modules:
            self.assertTrue(module["ordinary_source"].strip(), module["id"])
            self.assertNotIn("servicefabric_runtime", module["ordinary_source"])

    def test_each_lifecycle_transition_has_an_observable_assertion(self) -> None:
        assertions = {
            step["command"]: set(step["assertions"])
            for step in self.specification["journey"]
        }
        self.assertIn("prepared_lifecycle_state", assertions["dev prepare"])
        self.assertIn("running_lifecycle_state", assertions["dev start"])
        self.assertIn("preserved_module_state", assertions["dev status"])
        self.assertIn("preserved_module_state", assertions["dev restart"])
        self.assertIn("stopped_lifecycle_state", assertions["dev stop"])

    def test_collision_rollback_and_cleanup_are_non_destructive(self) -> None:
        safety = self.specification["safety"]
        self.assertEqual(
            safety["collision"],
            ["reject_existing_application", "leave_existing_files_unchanged"],
        )
        self.assertEqual(
            safety["rollback"],
            ["remove_partial_generated_files", "leave_no_application_registry_record"],
        )
        self.assertEqual(
            safety["cleanup"],
            [
                "remove_temporary_runtime_files",
                "preserve_generated_source",
                "preserve_build_manifest",
            ],
        )

    def test_build_manifest_is_immutable_and_digest_addressable(self) -> None:
        self.assertEqual(
            self.specification["build_manifest"],
            ["application_id", "source_digest", "output_digest", "modules", "immutable"],
        )


if __name__ == "__main__":
    unittest.main()


class FreshWorkspaceIntegrationTests(unittest.TestCase):
    """Execute the Wave-3 journey against the composed integration surface."""

    def test_research_notes_cli_journey(self) -> None:
        with tempfile.TemporaryDirectory(prefix="servicefabric-wave3-") as temporary:
            root = Path(temporary)
            dispatch(["--workspace", str(root), "workspace", "init"])
            created = dispatch([
                "--workspace", str(root), "apps", "create", "research-notes",
                "--template", "modular-web-app",
            ])[2]
            self.assertEqual(created["application_id"], "research-notes")

            layout = resolve_workspace(explicit_workspace=root).layout
            first_files = sorted(
                path.relative_to(layout.applications / "research-notes").as_posix()
                for path in (layout.applications / "research-notes").rglob("*")
                if path.is_file()
            )
            self.assertTrue((layout.applications / "research-notes/AGENTS.md").is_file())
            self.assertTrue((layout.applications / "research-notes/ARCHITECTURE.md").is_file())
            self.assertTrue((layout.applications / "research-notes/DEVELOPMENT.md").is_file())

            with self.assertRaises(ApplicationAlreadyExists):
                dispatch([
                    "--workspace", str(root), "apps", "create", "research-notes",
                    "--template", "modular-web-app",
                ])
            second_files = sorted(
                path.relative_to(layout.applications / "research-notes").as_posix()
                for path in (layout.applications / "research-notes").rglob("*")
                if path.is_file()
            )
            self.assertEqual(first_files, second_files)

            modules = dispatch(["--workspace", str(root), "apps", "modules", "research-notes"])[2]
            self.assertEqual(
                [module["id"] for module in modules["modules"]],
                ["notes-api", "notes-domain", "notes-web"],
            )
            self.assertTrue(dispatch(["--workspace", str(root), "apps", "validate", "research-notes"])[2]["valid"])
            dispatch(["--workspace", str(root), "apps", "dev", "prepare", "research-notes"])
            started = dispatch(["--workspace", str(root), "apps", "dev", "start", "research-notes"])[2]["start"]
            self.assertEqual(started["state"], "running")
            port = started["modules"]["notes-api"]["port"]

            with urlopen(Request(
                f"http://127.0.0.1:{port}/notes",
                data=b'{"title":"Integration","body":"integration note"}',
                headers={"Content-Type": "application/json"},
                method="POST",
            ), timeout=3) as response:
                self.assertEqual(json.loads(response.read())['body'], "integration note")
            with urlopen(f"http://127.0.0.1:{port}/notes?query=integration", timeout=3) as response:
                self.assertEqual(len(json.loads(response.read())["notes"]), 1)

            restarted = dispatch([
                "--workspace", str(root), "apps", "dev", "restart", "research-notes",
                "--module", "notes-api",
            ])[2]["restart"]
            self.assertEqual(restarted["state"], "running")
            with urlopen(f"http://127.0.0.1:{restarted['port']}/notes?query=integration", timeout=3) as response:
                self.assertEqual(len(json.loads(response.read())["notes"]), 1)

            build = dispatch(["--workspace", str(root), "apps", "build", "research-notes"])[2]["build"]
            self.assertTrue(build["artifact_digest"].startswith("sha256:"))
            self.assertEqual(
                build["artifact_digest"],
                dispatch(["--workspace", str(root), "apps", "build", "research-notes"])[2]["build"]["artifact_digest"],
            )
            stopped = dispatch(["--workspace", str(root), "apps", "dev", "stop", "research-notes"])[2]["stop"]
            self.assertEqual(stopped["state"], "stopped")
            status = dispatch(["--workspace", str(root), "apps", "dev", "status", "research-notes"])[2]["status"]
            self.assertEqual(status["state"], "stopped")
            self.assertIsNone(status["modules"]["notes-api"]["port"])
