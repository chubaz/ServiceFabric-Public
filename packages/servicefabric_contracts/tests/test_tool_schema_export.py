from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_contracts.schema_export import SCHEMA_RESOURCES, write_schema_snapshot


class ToolSchemaExportTests(unittest.TestCase):
    def test_lifecycle_schema_ids_are_stable(self) -> None:
        expected = {
            "tool-definition.schema.json": "https://schemas.servicefabric.ai/v1alpha1/tool-definition.schema.json",
            "tool-revision.schema.json": "https://schemas.servicefabric.ai/v1alpha1/tool-revision.schema.json",
            "tool-deployment.schema.json": "https://schemas.servicefabric.ai/v1alpha1/tool-deployment.schema.json",
            "tool-status.schema.json": "https://schemas.servicefabric.ai/v1alpha1/tool-status.schema.json",
        }
        self.assertEqual({name: SCHEMA_RESOURCES[name][1] for name in expected}, expected)

    def test_all_schema_snapshots_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            write_schema_snapshot(Path(first))
            write_schema_snapshot(Path(second))
            first_files = {path.name: path.read_bytes() for path in Path(first).glob("*.json")}
            second_files = {path.name: path.read_bytes() for path in Path(second).glob("*.json")}
            self.assertEqual(first_files, second_files)
