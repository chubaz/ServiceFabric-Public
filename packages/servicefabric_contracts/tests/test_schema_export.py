from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from servicefabric_contracts import ServicePackageDefinition
from servicefabric_contracts.schema_export import SCHEMA_RESOURCES, resource_schema, service_package_schema, write_schema_snapshot


class SchemaExportTests(unittest.TestCase):
    def test_schema_has_stable_identity_and_deterministic_output(self) -> None:
        self.assertEqual(service_package_schema()["$schema"], "https://json-schema.org/draft/2020-12/schema")
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_path = write_schema_snapshot(Path(first))
            second_path = write_schema_snapshot(Path(second))
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())

    def test_schema_index_hash_matches_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            schema_path = write_schema_snapshot(output)
            index = json.loads((output / "schema-index.json").read_text(encoding="utf-8"))
            service_entry = next(item for item in index["schemas"] if item["kind"] == "ServicePackageDefinition")
            self.assertEqual(service_entry["sha256"], hashlib.sha256(schema_path.read_bytes()).hexdigest())

    def test_schema_validates_representative_fixtures(self) -> None:
        fixtures = Path(__file__).parent / "fixtures"
        for fixture in sorted(fixtures.glob("*.json")):
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            matching = next((item for item in SCHEMA_RESOURCES.values() if item[3] == payload["kind"]), None)
            self.assertIsNotNone(matching)
            model, schema_id, title, _ = matching
            validator = Draft202012Validator(resource_schema(model, schema_id, title))
            with self.subTest(fixture=fixture.name):
                self.assertFalse(list(validator.iter_errors(payload)))
                model.model_validate(payload)
