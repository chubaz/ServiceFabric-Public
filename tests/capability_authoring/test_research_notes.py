from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_application_model",
    "servicefabric_framework_kits",
    "servicefabric_blueprints",
    "servicefabric_application_generator",
    "servicefabric_capability_authoring",
):
    sys.path.insert(0, str(ROOT / "packages" / package))

from servicefabric_application_generator import ApplicationGenerator, GenerationRequest, GenerationRollback
from servicefabric_blueprints import ApplicationBlueprint, BlueprintFile, RESEARCH_NOTES_BLUEPRINT
from servicefabric_capability_authoring import research_notes_declarations


class ResearchNotesCapabilityAuthoringTests(unittest.TestCase):
    def test_authors_exactly_three_explicit_operations_and_capabilities(self) -> None:
        declarations = research_notes_declarations()
        expected = {
            "notes.create": ("create-note", "database_write"),
            "notes.get": ("get-note", "database_read"),
            "notes.search": ("search-notes", "database_read"),
        }
        operations = {
            path: document
            for path, document in declarations.items()
            if path.startswith(".servicefabric/operations/")
        }
        capabilities = {
            path: document
            for path, document in declarations.items()
            if path.startswith(".servicefabric/capabilities/")
        }
        self.assertEqual(set(operations), {
            ".servicefabric/operations/create-note.yaml",
            ".servicefabric/operations/get-note.yaml",
            ".servicefabric/operations/search-notes.yaml",
        })
        self.assertEqual(set(capabilities), {
            ".servicefabric/capabilities/notes.create.yaml",
            ".servicefabric/capabilities/notes.get.yaml",
            ".servicefabric/capabilities/notes.search.yaml",
        })
        self.assertEqual(len(operations), 3)
        self.assertEqual(len(capabilities), 3)

        operation_ids = {document["metadata"]["id"] for document in operations.values()}
        for capability_id, (operation_id, effect_kind) in expected.items():
            document = declarations[f".servicefabric/capabilities/{capability_id}.yaml"]
            self.assertEqual(document["spec"]["operationRef"], operation_id)
            self.assertIn(document["spec"]["operationRef"], operation_ids)
            self.assertEqual(document["spec"]["effects"]["effects"][0]["effect_type"], effect_kind)
            self.assertEqual(set(document["metadata"]), {"id", "title", "domain"})
            self.assertTrue(document["spec"]["objective"])
            self.assertTrue(document["spec"]["concepts"])
            operation = declarations[f".servicefabric/operations/{operation_id}.yaml"]
            self.assertEqual(operation["metadata"]["version"], "1.0.0")
            self.assertEqual(set(operation["spec"]), {"application_ref", "module_ref", "interface_ref", "bindings"})
            self.assertEqual(len(operation["spec"]["bindings"]), 1)
            self.assertEqual(operation["spec"]["bindings"][0]["protocol"], "http")

    def test_only_reviewed_routes_are_exposed(self) -> None:
        declarations = research_notes_declarations()
        bindings = {
            document["metadata"]["id"]: document["spec"]["bindings"]
            for path, document in declarations.items()
            if path.startswith(".servicefabric/operations/")
        }
        self.assertEqual(bindings, {
            "create-note": [{
                "id": "create-note-http", "protocol": "http", "method": "POST",
                "path": "/notes", "request_schema_ref": "notes.create-note-input",
                "response_schema_ref": "notes.note-output", "timeout_seconds": 10,
            }],
            "get-note": [{
                "id": "get-note-http", "protocol": "http", "method": "GET",
                "path": "/notes/{note_id}", "request_schema_ref": "notes.get-note-input",
                "response_schema_ref": "notes.note-output", "timeout_seconds": 10,
            }],
            "search-notes": [{
                "id": "search-notes-http", "protocol": "http", "method": "GET",
                "path": "/notes", "request_schema_ref": "notes.search-notes-input",
                "response_schema_ref": "notes.search-notes-output", "timeout_seconds": 10,
            }],
        })

    def test_example_files_are_explicit_and_match_reviewed_declarations(self) -> None:
        declarations = research_notes_declarations()
        example_root = ROOT / "examples" / "research-notes"
        for relative, expected in declarations.items():
            path = example_root / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), expected)

    def test_referenced_input_and_output_schemas_are_valid_json_schema_documents(self) -> None:
        declarations = research_notes_declarations()
        schema_documents = {
            path: schema for path, schema in declarations.items() if path.endswith(".schema.json")
        }
        self.assertEqual(len(schema_documents), 5)
        self.assertEqual(
            json.dumps(schema_documents, sort_keys=True, separators=(",", ":")),
            json.dumps(
                {
                    path: schema
                    for path, schema in research_notes_declarations().items()
                    if path.endswith(".schema.json")
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        for relative, schema in declarations.items():
            if not relative.endswith(".schema.json"):
                continue
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertRegex(schema["$id"], r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
            self.assertEqual(schema["type"], "object")
            self.assertIn("properties", schema)
        for operation_id in ("create-note", "get-note", "search-notes"):
            operation = declarations[f".servicefabric/operations/{operation_id}.yaml"]
            for reference in (
                operation["spec"]["bindings"][0].get("request_schema_ref"),
                operation["spec"]["bindings"][0]["response_schema_ref"],
            ):
                self.assertIn(reference, {schema["$id"] for schema in schema_documents.values()})

    def test_generator_is_deterministic_and_creates_no_registry_records(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            result = ApplicationGenerator().generate(GenerationRequest(
                "research-notes", "Research Notes", RESEARCH_NOTES_BLUEPRINT, Path(first_directory)
            ))
            repeated = ApplicationGenerator().generate(GenerationRequest(
                "research-notes", "Research Notes", RESEARCH_NOTES_BLUEPRINT, Path(second_directory)
            ))
            expected = research_notes_declarations()
            for relative, document in expected.items():
                self.assertEqual(json.loads((result.root / relative).read_text(encoding="utf-8")), document)
            self.assertEqual(result.files, repeated.files)
            self.assertEqual(
                [path.read_bytes() for path in sorted(result.root.rglob("*")) if path.is_file()],
                [path.read_bytes() for path in sorted(repeated.root.rglob("*")) if path.is_file()],
            )
            self.assertFalse(any("registry" in path.parts for path in result.files))

    def test_generator_rolls_back_unsafe_static_manifest(self) -> None:
        blueprint = ApplicationBlueprint(
            blueprint_id=RESEARCH_NOTES_BLUEPRINT.blueprint_id,
            version=RESEARCH_NOTES_BLUEPRINT.version,
            title=RESEARCH_NOTES_BLUEPRINT.title,
            description=RESEARCH_NOTES_BLUEPRINT.description,
            modules=RESEARCH_NOTES_BLUEPRINT.modules,
            static_files=(BlueprintFile(".servicefabric/../registry.json", {}),),
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            with self.assertRaises(GenerationRollback):
                ApplicationGenerator().generate(GenerationRequest(
                    "research-notes", "Research Notes", blueprint, destination
                ))
            self.assertEqual(list(destination.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
