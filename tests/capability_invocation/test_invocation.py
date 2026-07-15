from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
for package in (
    ROOT / "packages/servicefabric_capability_invocation",
    ROOT / "packages/servicefabric_capability_registry/src",
    ROOT / "packages/servicefabric_capability_model/src",
    ROOT / "packages/servicefabric_operation_model",
):
    sys.path.insert(0, str(package))

from servicefabric_capability_invocation import (  # noqa: E402
    CapabilityAvailability,
    CapabilityInvocationRequest,
    CapabilityInvocationService,
    CapabilityUnavailableError,
    SchemaValidationError,
)
from servicefabric_capability_model import CapabilityDefinition  # noqa: E402
from servicefabric_capability_registry import CapabilityRegistry  # noqa: E402
from servicefabric_operation_model import HttpBinding, OperationDefinition  # noqa: E402


class InvocationFakes:
    def __init__(self, available: bool = True, output: object | None = None):
        self.available = available
        self.output = {"noteId": "n-1"} if output is None else output
        self.seen = []

    def resolve_operation(self, operation_id):
        return OperationDefinition(
            operation_id, "1.0.0", "research-notes", "api", "notes-api",
            (HttpBinding("z", "POST", "/notes", "request"), HttpBinding("a", "POST", "/notes", "request", "response")),
        )

    def resolve_availability(self, capability_id):
        return CapabilityAvailability(self.available, "http://127.0.0.1:8080" if self.available else None, "application stopped")

    def resolve_schema(self, schema_ref):
        return {
            "request": {"type": "object", "required": ["body"], "properties": {"body": {"type": "string", "minLength": 1}}, "additionalProperties": False},
            "response": {"type": "object", "required": ["noteId"], "properties": {"noteId": {"type": "string"}}},
        }[schema_ref]

    def invoke(self, request):
        self.seen.append(request)
        return self.output


def capability() -> CapabilityDefinition:
    return CapabilityDefinition.model_validate({
        "apiVersion": "servicefabric.local/v1", "kind": "CapabilityDefinition",
        "metadata": {"id": "notes.create", "title": "Create note", "domain": "research"},
        "spec": {
            "operationRef": "notes.create", "objective": "Create a research note.", "capabilityClass": "write",
            "concepts": ["note"], "expectedInputs": ["body"], "expectedOutputs": ["note id"],
            "effects": {"effects": [{"effect_type": "file_write", "target_category": "research-notes", "scope": "notes", "reversibility": "compensatable", "verification_required": False, "approval_required": False, "idempotency_required": False}]},
        },
    })


class CapabilityInvocationTests(unittest.TestCase):
    def service(self, fakes: InvocationFakes):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        registry = CapabilityRegistry(directory.name)
        registry.register(capability(), "research-notes")
        return CapabilityInvocationService(registry, fakes, fakes, fakes, fakes)

    def test_resolves_capability_operation_binding_and_endpoint_deterministically(self):
        fakes = InvocationFakes()
        result = self.service(fakes).invoke(CapabilityInvocationRequest("notes.create", {"body": "hello"}))
        self.assertEqual((result.capability_id, result.operation_id, result.binding_id, result.output), ("notes.create", "notes.create", "a", {"noteId": "n-1"}))
        self.assertEqual(fakes.seen[0].endpoint, "http://127.0.0.1:8080")

    def test_rejects_unavailable_capability_without_transport_call(self):
        fakes = InvocationFakes(available=False)
        with self.assertRaises(CapabilityUnavailableError):
            self.service(fakes).invoke(CapabilityInvocationRequest("notes.create", {"body": "hello"}))
        self.assertEqual(fakes.seen, [])

    def test_validates_input_before_transport(self):
        fakes = InvocationFakes()
        with self.assertRaises(SchemaValidationError):
            self.service(fakes).invoke(CapabilityInvocationRequest("notes.create", {"body": ""}))
        self.assertEqual(fakes.seen, [])

    def test_validates_transport_output(self):
        fakes = InvocationFakes(output={"wrong": "shape"})
        with self.assertRaises(SchemaValidationError):
            self.service(fakes).invoke(CapabilityInvocationRequest("notes.create", {"body": "hello"}, "a"))


if __name__ == "__main__":
    unittest.main()
