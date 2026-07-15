import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "packages/servicefabric_operation_model"))

from servicefabric_operation_model import (  # noqa: E402
    InvalidOperationDefinition,
    canonical_json,
    load_operation_definition_from_dict,
    serialize_operation_definition,
)


def manifest():
    return {
        "apiVersion": "servicefabric.local/v1", "kind": "OperationDefinition",
        "metadata": {"version": "1.0.0", "id": "notes.create", "name": "Create note"},
        "spec": {
            "interface_ref": "notes-api", "module_ref": "api", "application_ref": "research-notes",
            "bindings": [
                {"response_content_type": "application/json", "id": "public", "path": "/notes", "method": "POST", "protocol": "http", "timeout_seconds": 10}
            ],
        },
    }


class OperationDefinitionTests(unittest.TestCase):
    def test_loads_bounded_http_definition(self):
        definition = load_operation_definition_from_dict(manifest())
        self.assertEqual(definition.operation_id, "notes.create")
        self.assertEqual(definition.bindings[0].method, "POST")

    def test_unknown_fields_and_non_http_are_rejected(self):
        for mutate in (lambda value: value["spec"].update(extra=True), lambda value: value["spec"]["bindings"][0].update(protocol="mcp")):
            payload = manifest()
            mutate(payload)
            with self.assertRaises(InvalidOperationDefinition):
                load_operation_definition_from_dict(payload)

    def test_unsafe_paths_and_duplicate_bindings_are_rejected(self):
        for path in ("notes", "/notes//search", "/notes/../admin", "/notes?q=secret"):
            payload = manifest()
            payload["spec"]["bindings"][0]["path"] = path
            with self.assertRaises(InvalidOperationDefinition):
                load_operation_definition_from_dict(payload)
        payload = manifest()
        payload["spec"]["bindings"].append(dict(payload["spec"]["bindings"][0]))
        with self.assertRaises(InvalidOperationDefinition):
            load_operation_definition_from_dict(payload)

    def test_serialization_is_canonical_and_binding_order_is_stable(self):
        first = load_operation_definition_from_dict(manifest())
        payload = manifest()
        payload["spec"]["bindings"] = [{**payload["spec"]["bindings"][0], "id": "z"}, {**payload["spec"]["bindings"][0], "id": "a"}]
        second = load_operation_definition_from_dict(payload)
        self.assertEqual([item.binding_id for item in second.bindings], ["a", "z"])
        self.assertEqual(serialize_operation_definition(first), canonical_json(json.loads(serialize_operation_definition(first))))
        self.assertEqual(serialize_operation_definition(first), serialize_operation_definition(load_operation_definition_from_dict(json.loads(serialize_operation_definition(first)))))


if __name__ == "__main__":
    unittest.main()
