"""End-to-end Wave-6 acceptance journey for Research Notes projections."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen


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
for source in (
    ROOT / "packages" / "servicefabric_capability_consumers" / "src",
    ROOT / "packages" / "servicefabric_capability_mcp_projection" / "src",
    ROOT / "services" / "capability_rest_gateway" / "src",
    ROOT / "clients" / "python",
):
    sys.path.insert(0, str(source))

from servicefabric_capability_consumers import InternalAgentCapabilityReference
from servicefabric_capability_rest_gateway import LoopbackCapabilityRestServer
from servicefabric_client.capability_projections import CapabilityProjectionComposition
from servicefabric_client.main import dispatch
from servicefabric_workspace import resolve_workspace


class Wave06ResearchNotesAcceptanceTests(unittest.TestCase):
    def test_research_notes_has_one_canonical_result_across_all_projections(self) -> None:
        with tempfile.TemporaryDirectory(prefix="servicefabric-wave6-") as temporary:
            workspace = Path(temporary) / "workspace"
            environment = {"SERVICEFABRIC_WORKSPACE": str(workspace)}

            def call(*arguments: str):
                with patch.dict(os.environ, environment, clear=False):
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

            composition = CapabilityProjectionComposition.for_workspace(
                resolve_workspace(explicit_workspace=workspace).layout
            )
            self.assertEqual(
                [item.capability_id for item in composition.facade.list_capabilities("research-notes")],
                ["notes.create", "notes.get", "notes.search"],
            )

            call("apps", "dev", "prepare", "research-notes")
            _, started = call("apps", "dev", "start", "research-notes")
            self.assertEqual(started["start"]["state"], "running")

            mcp = composition.mcp_projection("research-notes")
            candidates = mcp.list_candidates()
            self.assertEqual(
                [(item.name, item.available) for item in candidates],
                [("notes.create", True), ("notes.get", True), ("notes.search", True)],
            )

            created = mcp.invoke(
                "notes.create",
                {"title": "Wave-6 journey", "body": "One canonical note across projections."},
            )
            mcp_search = mcp.invoke("notes.search", {"query": "Wave-6"})
            self.assertEqual(
                [note["id"] for note in mcp_search.output["notes"]],
                [created.output["id"]],
            )

            with LoopbackCapabilityRestServer(composition.rest_gateway) as server:
                rest_search = self._post_json(
                    f"{server.endpoint}/capabilities/notes.search/invoke", {"input": {"query": "Wave-6"}}
                )
                self.assertEqual(rest_search, self._canonical_json(mcp_search))

                client_search = composition.capability_client.invoke("notes.search", {"query": "Wave-6"})
                self.assertEqual(self._canonical_json(client_search), rest_search)

                reference = InternalAgentCapabilityReference("notes.search")
                self.assertEqual(reference.capability_id, client_search.capability_id)
                agent_search = composition.agent_adapter.invoke(reference, {"query": "Wave-6"})
                self.assertEqual(self._canonical_json(agent_search), rest_search)

                _, stopped = call("apps", "dev", "stop", "research-notes")
                self.assertEqual(stopped["stop"]["state"], "stopped")

                stopped_candidates = mcp.list_candidates()
                self.assertTrue(all(not item.available for item in stopped_candidates))
                for candidate in stopped_candidates:
                    availability = self._get_json(
                        f"{server.endpoint}/capabilities/{candidate.capability_id}/availability"
                    )
                    self.assertEqual(availability["state"], "unavailable")
                    self.assertFalse(
                        composition.agent_adapter.availability(
                            InternalAgentCapabilityReference(candidate.capability_id)
                        ).available
                    )
                self.assertTrue(all(not item.available for item in composition.capability_client.discover("research-notes")))

            self.assertEqual(
                [item.capability_id for item in composition.facade.list_capabilities("research-notes")],
                ["notes.create", "notes.get", "notes.search"],
            )
            _, existing_mcp = call("mcp", "tools", "list")
            self.assertIn("math.calculate", [tool.name for tool in existing_mcp["tools"]])

    @staticmethod
    def _canonical_json(invocation: object) -> dict[str, object]:
        return {
            "bindingId": invocation.binding_id,
            "capabilityId": invocation.capability_id,
            "operationId": invocation.operation_id,
            "output": Wave06ResearchNotesAcceptanceTests._json_value(invocation.output),
        }

    @staticmethod
    def _json_value(value: object) -> object:
        if isinstance(value, Mapping):
            return {str(key): Wave06ResearchNotesAcceptanceTests._json_value(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [Wave06ResearchNotesAcceptanceTests._json_value(item) for item in value]
        return value

    @staticmethod
    def _get_json(url: str) -> dict[str, object]:
        with urlopen(url, timeout=2) as response:
            return json.load(response)

    @staticmethod
    def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            return json.load(response)


if __name__ == "__main__":
    unittest.main()
