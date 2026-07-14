"""Tests for built-in reviewed blueprint module manifests."""

from __future__ import annotations

import unittest
from pathlib import Path

from servicefabric_blueprints import (
    RESEARCH_NOTES_BLUEPRINT,
    TEXT_UTILITY_BLUEPRINT,
)


class TestBlueprintModules(unittest.TestCase):
    def test_text_utility_loads_as_valid_fastapi_service_module(self) -> None:
        modules = TEXT_UTILITY_BLUEPRINT.load_modules()

        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0].module_id, "text-api")
        self.assertEqual(modules[0].primitive, "service")
        self.assertEqual(modules[0].source, "examples/text-utility")

    def test_research_notes_declares_local_resource_dependency(self) -> None:
        modules = RESEARCH_NOTES_BLUEPRINT.load_modules()

        self.assertEqual(len(modules), 1)
        notes_api = modules[0]
        self.assertEqual(notes_api.module_id, "notes-api")
        self.assertEqual([resource.id for resource in notes_api.resources], ["notes-db"])
        self.assertEqual(notes_api.lifecycle.start_after, ("notes-db",))

    def test_manifest_results_are_caller_owned(self) -> None:
        manifest = TEXT_UTILITY_BLUEPRINT.module_manifest("text-api")
        manifest["metadata"]["id"] = "mutated-api"

        fresh_manifest = TEXT_UTILITY_BLUEPRINT.module_manifest("text-api")

        self.assertEqual(fresh_manifest["metadata"]["id"], "text-api")

    def test_builtin_blueprint_sources_exist(self) -> None:
        root = Path(__file__).resolve().parents[2]

        for blueprint in (RESEARCH_NOTES_BLUEPRINT, TEXT_UTILITY_BLUEPRINT):
            for module in blueprint.load_modules():
                self.assertTrue((root / module.source).is_dir(), module.source)


if __name__ == "__main__":
    unittest.main()
