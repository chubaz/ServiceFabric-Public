from __future__ import annotations

import unittest

from pydantic import ValidationError

from servicefabric_contracts import ToolDefinition
from test_service_package import load_fixture


class ToolDefinitionTests(unittest.TestCase):
    def test_reference_definitions_validate(self) -> None:
        for name in ("tool_definition_math_calculate.json", "tool_definition_research_search_papers.json", "tool_definition_project_create_task.json"):
            with self.subTest(name=name):
                definition = ToolDefinition.model_validate(load_fixture(name))
                self.assertEqual(definition.metadata.id, definition.spec.tool_id)

    def test_mcp_projection_defaults_off(self) -> None:
        definition = ToolDefinition.model_validate(load_fixture("tool_definition_math_calculate.json"))
        self.assertFalse(definition.spec.mcp_projection.expose)

    def test_definition_rejects_deployment_routing(self) -> None:
        payload = load_fixture("tool_definition_math_calculate.json")
        payload["spec"]["traffic_policy"] = {"traffic_kind": "single"}
        with self.assertRaises(ValidationError):
            ToolDefinition.model_validate(payload)

    def test_stable_tool_identity_cannot_embed_revision(self) -> None:
        payload = load_fixture("tool_definition_math_calculate.json")
        payload["metadata"]["id"] = "math.calculate.v1"
        payload["spec"]["tool_id"] = "math.calculate.v1"
        with self.assertRaises(ValidationError):
            ToolDefinition.model_validate(payload)

    def test_duplicate_permissions_are_rejected(self) -> None:
        payload = load_fixture("tool_definition_research_search_papers.json")
        permission = payload["spec"]["required_permissions"]["permissions"][0].copy()
        payload["spec"]["required_permissions"]["permissions"].append(permission)
        with self.assertRaises(ValidationError):
            ToolDefinition.model_validate(payload)

    def test_mcp_projection_rejects_execution_endpoint(self) -> None:
        payload = load_fixture("tool_definition_research_search_papers.json")
        payload["spec"]["mcp_projection"]["endpoint"] = "https://mcp.example"
        with self.assertRaises(ValidationError):
            ToolDefinition.model_validate(payload)

    def test_unknown_lifecycle_fields_are_rejected(self) -> None:
        payload = load_fixture("tool_definition_math_calculate.json")
        payload["spec"]["lifecycle"]["active_revision"] = "1.0.0"
        with self.assertRaises(ValidationError):
            ToolDefinition.model_validate(payload)
