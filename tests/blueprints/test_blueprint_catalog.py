"""Tests for reviewed blueprint catalog behavior."""

from __future__ import annotations

import unittest

from servicefabric_blueprints import (
    BlueprintCatalog,
    BlueprintNotFound,
    DuplicateBlueprintRegistration,
    TEXT_UTILITY_BLUEPRINT,
    create_default_blueprint_catalog,
)


class TestBlueprintCatalog(unittest.TestCase):
    def test_default_catalog_contains_reviewed_blueprints(self) -> None:
        catalog = create_default_blueprint_catalog()

        blueprints = catalog.list()

        self.assertEqual(
            [blueprint.blueprint_id for blueprint in blueprints],
            ["research-notes", "text-utility"],
        )

    def test_resolve_requires_exact_blueprint_version(self) -> None:
        catalog = create_default_blueprint_catalog()

        blueprint = catalog.resolve("text-utility", "0.1.0")

        self.assertEqual(blueprint, TEXT_UTILITY_BLUEPRINT)
        with self.assertRaises(BlueprintNotFound):
            catalog.resolve("text-utility", "9.9.9")

    def test_reject_duplicate_blueprint_registration(self) -> None:
        catalog = BlueprintCatalog()
        catalog.register(TEXT_UTILITY_BLUEPRINT)

        with self.assertRaises(DuplicateBlueprintRegistration):
            catalog.register(TEXT_UTILITY_BLUEPRINT)


if __name__ == "__main__":
    unittest.main()
