"""End-to-end Wave-2 journey for the reviewed Research Notes application."""

from __future__ import annotations

import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_application_assembly",
    "servicefabric_application_model",
    "servicefabric_artifacts",
    "servicefabric_blueprints",
    "servicefabric_contracts",
    "servicefabric_framework_kits",
    "servicefabric_process_runtime",
    "servicefabric_resource_bindings",
    "servicefabric_workspace",
):
    sys.path.insert(0, str(ROOT / "packages" / package))
sys.path.insert(0, str(ROOT / "packages" / "servicefabric_contracts" / "src"))
sys.path.insert(0, str(ROOT / "services" / "application_dev_supervisor"))
sys.path.insert(0, str(ROOT / "clients" / "python"))

from servicefabric_client.development import APPLICATION_ID, ResearchNotesDevelopmentService
from servicefabric_client.main import dispatch
from servicefabric_workspace import WorkspaceService, resolve_workspace


class ResearchNotesRuntimeJourneyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.context = resolve_workspace(explicit_workspace=self.root)
        WorkspaceService(self.context).initialize()
        self.service = ResearchNotesDevelopmentService(self.context.layout)

    def tearDown(self) -> None:
        try:
            self.service.stop()
        finally:
            self.temporary.cleanup()

    def test_prepare_start_restart_and_stop_preserve_application_boundaries(self) -> None:
        prepared = self.service.prepare()
        self.assertEqual(prepared["resources"], {"notes-db": "ready"})
        self.assertEqual(tuple(self.service.assembly.build_order), ("notes-domain", "notes-api", "notes-web"))
        self.assertTrue((self.context.layout.builds / APPLICATION_ID / "assembly.json").is_file())
        self.assertTrue((self.context.layout.bindings / APPLICATION_ID / "resolved-bindings.json").is_file())

        started = self.service.start()
        self.assertEqual(started["state"], "running")
        self.assertEqual(started["modules"]["notes-domain"]["state"], "ready")
        self.assertEqual(started["modules"]["notes-api"]["health"], "healthy")
        self.assertEqual(started["modules"]["notes-web"]["health"], "healthy")
        self.assertLess(started["modules"]["notes-api"]["port"], 65536)
        self.assertLess(started["modules"]["notes-web"]["port"], 65536)

        api_port = started["modules"]["notes-api"]["port"]
        web_before = self.service.processes.status(APPLICATION_ID, "notes-web").identity
        self.assertIsNotNone(web_before)
        self._request_json(
            api_port,
            "/notes",
            method="POST",
            body={"title": "Runtime plan", "body": "SQLite survives API restart."},
        )
        found = self._request_json(api_port, "/notes?query=sqlite")
        self.assertEqual([note["title"] for note in found["notes"]], ["Runtime plan"])

        restarted = ResearchNotesDevelopmentService(self.context.layout)
        api_record = restarted.restart("notes-api")
        self.assertEqual(api_record["state"], "running")
        self.assertEqual(api_record["health"], "healthy")
        web_after = restarted.processes.status(APPLICATION_ID, "notes-web").identity
        self.assertEqual(web_after, web_before)
        found_after = self._request_json(api_record["port"], "/notes?query=sqlite")
        self.assertEqual([note["title"] for note in found_after["notes"]], ["Runtime plan"])

        stopped = restarted.stop()
        self.assertEqual(stopped["state"], "stopped")
        self.assertEqual(restarted.processes.status(APPLICATION_ID, "notes-api").state, "stopped")
        self.assertEqual(restarted.processes.status(APPLICATION_ID, "notes-web").state, "stopped")
        self.assertTrue((self.context.layout.bindings / APPLICATION_ID / "sqlite" / "notes-db.sqlite3").is_file())

    def test_cli_delegates_the_required_development_commands(self) -> None:
        commands = (
            ("prepare", ("prepare", APPLICATION_ID)),
            ("start", ("start", APPLICATION_ID)),
            ("status", ("status", APPLICATION_ID)),
            ("restart", ("restart", APPLICATION_ID, "--module", "notes-api")),
            ("stop", ("stop", APPLICATION_ID)),
        )
        for action, suffix in commands:
            code, command, value = dispatch([
                "--workspace", str(self.root), "apps", "dev", *suffix,
            ])
            self.assertEqual(code, 0)
            self.assertEqual(command, f"apps-dev-{action}")
            self.assertIn(action, value)

    @staticmethod
    def _request_json(port: int, path: str, *, method: str = "GET", body: dict[str, str] | None = None) -> dict[str, object]:
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            data=payload,
            method=method,
            headers={"Content-Type": "application/json"} if payload else {},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
