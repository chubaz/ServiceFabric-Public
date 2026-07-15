"""Wave-4 CLI acceptance coverage for static application capabilities."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from servicefabric_client.main import dispatch


class CapabilityCliAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name) / "workspace"
        self.environment = {
            "SERVICEFABRIC_WORKSPACE": str(self.workspace),
            "SERVICEFABRIC_HOME": None,
        }
        self.call("workspace", "init", str(self.workspace))
        self.call("apps", "create", "research-notes", "--template", "modular-web-app")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def call(self, *arguments: str):
        with patch.dict(
            os.environ,
            {key: value for key, value in self.environment.items() if value is not None},
            clear=False,
        ):
            os.environ.pop("SERVICEFABRIC_HOME", None)
            code, command, value = dispatch(list(arguments))
        self.assertEqual(code, 0, (arguments, value))
        return command, value

    def test_generated_research_notes_validates_and_registers_exactly_three_static_definitions(self) -> None:
        command, validation = self.call("capabilities", "validate", "research-notes")
        self.assertEqual(command, "capabilities-validate")
        self.assertEqual(validation["operations"], ["create-note", "get-note", "search-notes"])
        self.assertEqual(validation["capabilities"], ["notes.create", "notes.get", "notes.search"])
        self.assertFalse((self.workspace / ".servicefabric/registry/capabilities/capability-registry.json").exists())

        _, registered = self.call("capabilities", "register", "research-notes")
        self.assertEqual(
            [item["metadata"]["id"] for item in registered["capabilities"]],
            ["notes.create", "notes.get", "notes.search"],
        )
        effects = {
            item["metadata"]["id"]: item["spec"]["effects"]["effects"][0]["effect_type"]
            for item in registered["capabilities"]
        }
        self.assertEqual(effects, {
            "notes.create": "database_write",
            "notes.get": "database_read",
            "notes.search": "database_read",
        })
        self.assertEqual(
            {item["spec"]["operationRef"] for item in registered["capabilities"]},
            {"create-note", "get-note", "search-notes"},
        )

    def test_registration_is_idempotent_and_listing_and_describe_are_deterministic(self) -> None:
        _, first = self.call("capabilities", "register", "research-notes")
        _, second = self.call("capabilities", "register", "research-notes")
        self.assertEqual(first["digests"], second["digests"])

        _, listed = self.call("capabilities", "list")
        self.assertEqual(
            [item["metadata"]["id"] for item in listed["capabilities"]],
            ["notes.create", "notes.get", "notes.search"],
        )
        _, scoped = self.call("capabilities", "list", "--application", "research-notes")
        self.assertEqual(scoped["capabilities"], listed["capabilities"])
        _, described = self.call("capabilities", "describe", "notes.create")
        self.assertEqual(described["capability"], listed["capabilities"][0])

    def test_conflicting_identity_reuse_is_rejected_without_replacing_registered_definition(self) -> None:
        self.call("capabilities", "register", "research-notes")
        capability_path = self.workspace / "applications/research-notes/.servicefabric/capabilities/notes.create.yaml"
        payload = json.loads(capability_path.read_text(encoding="utf-8"))
        payload["spec"]["objective"] = "A conflicting identity reuse."
        capability_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

        with self.assertRaises(Exception) as raised:
            self.call("capabilities", "register", "research-notes")
        self.assertIn("already registered with different content", str(raised.exception))
        _, described = self.call("capabilities", "describe", "notes.create")
        self.assertNotEqual(described["capability"]["spec"]["objective"], payload["spec"]["objective"])

    def test_stopping_application_does_not_remove_definitions_or_create_tool_or_mcp_projections(self) -> None:
        self.call("capabilities", "register", "research-notes")
        self.call("apps", "dev", "stop", "research-notes")
        _, listed = self.call("capabilities", "list")
        self.assertEqual(len(listed["capabilities"]), 3)
        self.assertFalse((self.workspace / ".servicefabric/mcp").exists())
        self.assertFalse((self.workspace / ".servicefabric/tools").exists())
        self.assertTrue(all(item["kind"] == "CapabilityDefinition" for item in listed["capabilities"]))


if __name__ == "__main__":
    unittest.main()
