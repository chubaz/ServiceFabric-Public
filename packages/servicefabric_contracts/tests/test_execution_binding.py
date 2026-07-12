from __future__ import annotations

import unittest

from pydantic import TypeAdapter, ValidationError

from servicefabric_contracts.execution_binding import ExecutionBinding


class ExecutionBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = TypeAdapter(ExecutionBinding)

    def test_all_bounded_variants_validate(self) -> None:
        variants = [
            {"binding_kind": "native_function", "service_package_id": "package-a", "entrypoint_id": "library", "function_ref": "calculate"},
            {"binding_kind": "native_service", "service_package_id": "package-a", "entrypoint_id": "api", "operation_ref": "lookup"},
            {"binding_kind": "internal_graph", "graph_revision_ref": "graph://research/42"},
            {"binding_kind": "external_http", "external_binding_ref": "provider-a", "path_template": "/search/{query}", "method": "GET"},
            {"binding_kind": "database_operation", "service_package_id": "package-a", "entrypoint_id": "database", "operation_id": "lookup-record"},
            {"binding_kind": "command_runner", "service_package_id": "package-a", "entrypoint_id": "cli", "command_name": "calculate", "argument_mapping": [{"argument": "expression", "input_field_ref": "input.expression"}]},
            {"binding_kind": "federated_mcp", "external_package_id": "external-mcp", "remote_tool_name": "research.search", "projection_policy": "explicit_selection"},
            {"binding_kind": "human_task", "workflow_ref": "review-workflow", "task_type": "review", "result_handling": "human_validated"},
        ]
        for payload in variants:
            with self.subTest(kind=payload["binding_kind"]):
                self.adapter.validate_python(payload)

    def test_raw_shell_sql_and_credentials_are_rejected(self) -> None:
        invalid = [
            {"binding_kind": "command_runner", "service_package_id": "p", "entrypoint_id": "cli", "command_name": "run", "shell_command": "rm -rf /"},
            {"binding_kind": "database_operation", "service_package_id": "p", "entrypoint_id": "db", "operation_id": "lookup", "sql": "SELECT * FROM users"},
            {"binding_kind": "external_http", "external_binding_ref": "provider", "path_template": "/", "method": "GET", "bearer_token": "secret"},
        ]
        for payload in invalid:
            with self.subTest(kind=payload["binding_kind"]), self.assertRaises(ValidationError):
                self.adapter.validate_python(payload)

    def test_federated_mcp_requires_selected_remote_tool(self) -> None:
        with self.assertRaises(ValidationError):
            self.adapter.validate_python({"binding_kind": "federated_mcp", "external_package_id": "external-mcp", "projection_policy": "explicit_selection"})

    def test_managed_binding_requires_package_owner(self) -> None:
        with self.assertRaises(ValidationError):
            self.adapter.validate_python({"binding_kind": "native_function", "entrypoint_id": "library", "function_ref": "calculate"})
