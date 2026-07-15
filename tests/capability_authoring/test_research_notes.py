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

from servicefabric_application_generator import ApplicationGenerator, GenerationRequest
from servicefabric_blueprints import RESEARCH_NOTES_BLUEPRINT
from servicefabric_capability_authoring import research_notes_declarations


class ResearchNotesCapabilityAuthoringTests(unittest.TestCase):
    def test_explicit_capabilities_reference_their_exact_operations(self) -> None:
        declarations = research_notes_declarations()
        expected = {
            "notes.create": ("create-note", "data.write"),
            "notes.get": ("get-note", "data.read"),
            "notes.search": ("search-notes", "data.read"),
        }
        for capability_id, (operation_id, effect_kind) in expected.items():
            document = declarations[f".servicefabric/capabilities/{capability_id}.yaml"]
            self.assertEqual(document["spec"]["operationRef"], operation_id)
            self.assertEqual(document["spec"]["effects"][0]["kind"], effect_kind)
            operation = declarations[f".servicefabric/operations/{operation_id}.yaml"]
            self.assertEqual(operation["spec"]["effects"][0]["kind"], effect_kind)

    def test_example_files_are_explicit_and_match_reviewed_declarations(self) -> None:
        declarations = research_notes_declarations()
        example_root = ROOT / "examples" / "research-notes"
        for relative, expected in declarations.items():
            path = example_root / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), expected)

    def test_referenced_input_and_output_schemas_are_valid_json_schema_documents(self) -> None:
        declarations = research_notes_declarations()
        for relative, schema in declarations.items():
            if not relative.endswith(".schema.json"):
                continue
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")
            self.assertIn("properties", schema)
        for operation_id in ("create-note", "get-note", "search-notes"):
            operation = declarations[f".servicefabric/operations/{operation_id}.yaml"]
            for reference in (operation["spec"]["inputSchemaRef"], operation["spec"]["outputSchemaRef"]):
                self.assertIn(f".servicefabric/{reference}", declarations)

    def test_generator_materializes_only_reviewed_static_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = ApplicationGenerator().generate(
                GenerationRequest("research-notes", "Research Notes", RESEARCH_NOTES_BLUEPRINT, Path(directory))
            )
            expected = research_notes_declarations()
            for relative, document in expected.items():
                self.assertEqual(json.loads((result.root / relative).read_text(encoding="utf-8")), document)
            generated = "\n".join(path.as_posix() for path in result.files)
            self.assertNotIn("registry", generated)
            self.assertNotIn("mcp", generated)


if __name__ == "__main__":
    unittest.main()
