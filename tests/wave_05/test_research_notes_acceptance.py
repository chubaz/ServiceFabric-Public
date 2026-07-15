"""End-to-end Wave-5 acceptance journey for Research Notes capabilities."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_application_assembly",
    "servicefabric_application_model",
    "servicefabric_artifacts",
    "servicefabric_blueprints",
    "servicefabric_capability_authoring",
    "servicefabric_capability_invocation",
    "servicefabric_contracts",
    "servicefabric_framework_kits",
    "servicefabric_operation_model",
    "servicefabric_process_runtime",
    "servicefabric_resource_bindings",
    "servicefabric_workspace",
):
    sys.path.insert(0, str(ROOT / "packages" / package))
for package in (
    "servicefabric_capability_model",
    "servicefabric_capability_registry",
    "servicefabric_capability_runtime",
    "servicefabric_http_operation_adapter",
):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))
sys.path.insert(0, str(ROOT / "clients" / "python"))

from servicefabric_capability_invocation import SchemaValidationError
from servicefabric_client.main import dispatch
from servicefabric_http_operation_adapter import HttpOperationAdapter


class ResearchNotesCapabilityJourneyTests(unittest.TestCase):
    def test_registered_capabilities_follow_the_running_application_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="servicefabric-wave5-") as temporary:
            workspace = Path(temporary) / "workspace"
            environment = {
                "SERVICEFABRIC_WORKSPACE": str(workspace),
                "SERVICEFABRIC_HOME": None,
            }

            def call(*arguments: str):
                with patch.dict(os.environ, {key: value for key, value in environment.items() if value is not None}, clear=False):
                    os.environ.pop("SERVICEFABRIC_HOME", None)
                    code, command, value = dispatch(list(arguments))
                self.assertEqual(code, 0, (arguments, value))
                return command, value

            call("workspace", "init", str(workspace))
            call("apps", "create", "research-notes", "--template", "modular-web-app")
            _, registered = call("capabilities", "register", "research-notes")
            self.assertEqual(
                [item["metadata"]["id"] for item in registered["capabilities"]],
                ["notes.create", "notes.get", "notes.search"],
            )

            call("apps", "dev", "prepare", "research-notes")
            _, started = call("apps", "dev", "start", "research-notes")
            self.assertEqual(started["state"], "running")
            _, available = call("capabilities", "availability", "--application", "research-notes")
            self.assertEqual(
                [(item["capabilityId"], item["state"]) for item in available["capabilities"]],
                [("notes.create", "available"), ("notes.get", "available"), ("notes.search", "available")],
            )

            original_invoke = HttpOperationAdapter.invoke
            with patch.object(HttpOperationAdapter, "invoke", autospec=True, side_effect=original_invoke) as transport:
                _, created = call(
                    "capabilities", "invoke", "notes.create",
                    "--input", '{"title":"Wave-5 journey","body":"A capability invocation reaches Research Notes."}',
                )
                self.assertEqual(created["invocation"]["output"]["title"], "Wave-5 journey")

                _, searched = call(
                    "capabilities", "invoke", "notes.search", "--input", '{"query":"Wave-5"}',
                )
                self.assertEqual(
                    [note["id"] for note in searched["invocation"]["output"]["notes"]],
                    [created["invocation"]["output"]["id"]],
                )

                calls_before_invalid_input = transport.call_count
                with self.assertRaises(SchemaValidationError):
                    call(
                        "capabilities", "invoke", "notes.create",
                        "--input", '{"title":"","body":"Rejected before HTTP."}',
                    )
                self.assertEqual(transport.call_count, calls_before_invalid_input)

            _, stopped = call("apps", "dev", "stop", "research-notes")
            self.assertEqual(stopped["state"], "stopped")
            _, unavailable = call("capabilities", "availability", "--application", "research-notes")
            self.assertEqual(
                [(item["capabilityId"], item["state"]) for item in unavailable["capabilities"]],
                [("notes.create", "unavailable"), ("notes.get", "unavailable"), ("notes.search", "unavailable")],
            )
            _, listed = call("capabilities", "list", "--application", "research-notes")
            self.assertEqual(
                [item["metadata"]["id"] for item in listed["capabilities"]],
                ["notes.create", "notes.get", "notes.search"],
            )


if __name__ == "__main__":
    unittest.main()
