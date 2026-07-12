from __future__ import annotations

import unittest

from pydantic import ValidationError

from servicefabric_contracts import ServicePackageDefinition, ToolDefinition, ToolRevision
from test_service_package import load_fixture


class ToolInvariantTests(unittest.TestCase):
    def test_none_effect_cannot_coexist_with_write(self) -> None:
        payload = load_fixture("tool_revision_project_create_task_v1.json")
        payload["spec"]["effect_contract"]["effects"].insert(0, {"effect_type": "none", "target_category": "none", "scope": "none", "reversibility": "not_applicable", "verification_required": False, "approval_required": False, "idempotency_required": False})
        with self.assertRaises(ValidationError):
            ToolRevision.model_validate(payload)

    def test_irreversible_effect_cannot_claim_safe_retry(self) -> None:
        payload = load_fixture("tool_revision_project_create_task_v1.json")
        payload["spec"]["effect_contract"]["effects"][0]["reversibility"] = "irreversible"
        payload["spec"]["idempotency"]["retry_safety"] = "safe"
        with self.assertRaises(ValidationError):
            ToolRevision.model_validate(payload)

    def test_effectful_revision_cannot_leave_idempotency_unknown(self) -> None:
        payload = load_fixture("tool_revision_project_create_task_v1.json")
        payload["spec"]["idempotency"]["idempotency_class"] = "unknown"
        with self.assertRaises(ValidationError):
            ToolRevision.model_validate(payload)

    def test_one_package_can_implement_multiple_tools(self) -> None:
        math = ToolRevision.model_validate(load_fixture("tool_revision_math_calculate_v1.json"))
        project_payload = load_fixture("tool_revision_project_create_task_v1.json")
        project_payload["spec"]["package_ref"]["package_id"] = "math-runtime"
        project_payload["spec"]["execution_binding"]["service_package_id"] = "math-runtime"
        project = ToolRevision.model_validate(project_payload)
        self.assertEqual(math.spec.package_ref.package_id, project.spec.package_ref.package_id)
        self.assertNotEqual(math.spec.tool_id, project.spec.tool_id)

    def test_frontend_package_can_implement_zero_tools(self) -> None:
        package = ServicePackageDefinition.model_validate(load_fixture("frontend_only_svelte.json"))
        tools: tuple[ToolRevision, ...] = ()
        self.assertEqual(package.spec.hosting.mode, "managed_static")
        self.assertEqual(tools, ())

    def test_package_hosting_does_not_imply_mcp_projection(self) -> None:
        package = ServicePackageDefinition.model_validate(load_fixture("managed_http_capsule.json"))
        definition = ToolDefinition.model_validate(load_fixture("tool_definition_math_calculate.json"))
        self.assertEqual(package.spec.hosting.mode, "managed_container")
        self.assertFalse(definition.spec.mcp_projection.expose)

    def test_cli_becomes_tool_only_through_bounded_command(self) -> None:
        payload = load_fixture("tool_revision_math_calculate_v1.json")
        payload["spec"]["package_ref"] = {"package_id": "finance-cli", "package_version": "1.0.0", "entrypoint_id": "calculate"}
        payload["spec"]["execution_binding"] = {"binding_kind": "command_runner", "service_package_id": "finance-cli", "entrypoint_id": "calculate", "command_name": "calculate", "argument_mapping": [{"argument": "expression", "input_field_ref": "input.expression"}]}
        revision = ToolRevision.model_validate(payload)
        self.assertEqual(revision.spec.execution_binding.binding_kind, "command_runner")

    def test_external_mcp_selects_one_remote_tool(self) -> None:
        payload = load_fixture("tool_revision_research_search_papers_v1.json")
        payload["spec"]["package_ref"] = {"package_id": "federated-research", "package_version": "1.0.0", "entrypoint_id": "server"}
        payload["spec"]["execution_binding"] = {"binding_kind": "federated_mcp", "external_package_id": "federated-research", "remote_tool_name": "research.search_papers", "projection_policy": "explicit_selection"}
        revision = ToolRevision.model_validate(payload)
        self.assertEqual(revision.spec.execution_binding.remote_tool_name, "research.search_papers")
