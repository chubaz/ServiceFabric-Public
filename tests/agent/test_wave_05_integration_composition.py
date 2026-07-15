from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from servicefabric_client.capability_runtime import CapabilityRuntimeService
from servicefabric_capability_invocation import SchemaValidationError
from servicefabric_http_operation_adapter import HttpOperationAdapter
from servicefabric_process_runtime import ProcessStatus
from servicefabric_workspace import resolve_workspace

from servicefabric_client.main import dispatch


class _ProcessStatuses:
    def __init__(self, status: ProcessStatus) -> None:
        self.status_value = status

    def status(self, application_id: str, module_id: str) -> ProcessStatus:
        self.last_lookup = (application_id, module_id)
        return self.status_value


class Wave05IntegrationCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name) / "workspace"
        self.environment = {"SERVICEFABRIC_WORKSPACE": str(self.workspace), "SERVICEFABRIC_HOME": None}
        self.call("workspace", "init", str(self.workspace))
        self.call("apps", "create", "research-notes", "--template", "modular-web-app")
        self.call("capabilities", "register", "research-notes")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def call(self, *arguments: str):
        with patch.dict(os.environ, {key: value for key, value in self.environment.items() if value is not None}, clear=False):
            os.environ.pop("SERVICEFABRIC_HOME", None)
            return dispatch(list(arguments))

    def service(self, status: ProcessStatus) -> CapabilityRuntimeService:
        with patch.dict(os.environ, {"SERVICEFABRIC_WORKSPACE": str(self.workspace)}, clear=False):
            os.environ.pop("SERVICEFABRIC_HOME", None)
            context = resolve_workspace()
        return CapabilityRuntimeService(context.layout, processes=_ProcessStatuses(status))  # type: ignore[arg-type]

    def test_healthy_owning_module_is_available(self) -> None:
        service = self.service(ProcessStatus("running", None, 8111, "healthy", 1.0))

        availability = service.availability("notes.create")

        self.assertTrue(availability.available)
        self.assertEqual(availability.to_dict()["reason"], "module_healthy")

    def test_stopped_module_is_unavailable_without_unregistering_definition(self) -> None:
        service = self.service(ProcessStatus("stopped", None, None, "unavailable", None))

        availability = service.availability("notes.create")
        _, _, listed = self.call("capabilities", "list", "--application", "research-notes")

        self.assertFalse(availability.available)
        self.assertEqual(availability.to_dict()["reason"], "module_stopped")
        self.assertEqual([item["metadata"]["id"] for item in listed["capabilities"]], ["notes.create", "notes.get", "notes.search"])

    def test_cli_invokes_valid_input_through_reviewed_transport(self) -> None:
        status = _ProcessStatuses(ProcessStatus("running", None, 8111, "healthy", 1.0))
        output = {"id": 1, "title": "One", "body": "Body", "created_at": "2026-07-15T00:00:00Z"}
        with patch("servicefabric_client.capability_runtime.ManagedProcessController", return_value=status), patch.object(
            HttpOperationAdapter, "invoke", return_value=output
        ) as transport:
            code, command, value = self.call(
                "capabilities", "invoke", "notes.create", "--input", '{"title":"One","body":"Body"}'
            )

        self.assertEqual((code, command), (0, "capabilities-invoke"))
        self.assertEqual(value["invocation"]["output"], output)
        transport.assert_called_once()

    def test_cli_rejects_invalid_input_before_transport(self) -> None:
        status = _ProcessStatuses(ProcessStatus("running", None, 8111, "healthy", 1.0))
        with patch("servicefabric_client.capability_runtime.ManagedProcessController", return_value=status), patch.object(
            HttpOperationAdapter, "invoke"
        ) as transport:
            with self.assertRaises(SchemaValidationError):
                self.call("capabilities", "invoke", "notes.create", "--input", '{"title":"","body":"Body"}')

        transport.assert_not_called()
