"""Unit tests for identifier validation."""

from __future__ import annotations

import unittest

from servicefabric_workspace.errors import InvalidApplicationId
from servicefabric_workspace.identifiers import validate_application_id


class TestIdentifiers(unittest.TestCase):
    def test_valid_identifiers(self) -> None:
        self.assertEqual(validate_application_id("research-notes"), "research-notes")
        self.assertEqual(validate_application_id("financial-analytics"), "financial-analytics")
        self.assertEqual(validate_application_id("app2"), "app2")
        self.assertEqual(validate_application_id("document-manager-2"), "document-manager-2")

    def test_invalid_identifiers(self) -> None:
        invalid_ids = [
            "",
            "Research-Notes",
            "research_notes",
            "../research-notes",
            "/research-notes",
            "research--notes",
            "research-",
            "-research",
            "re",  # too short
            "a" * 64,  # too long
        ]
        for val in invalid_ids:
            with self.assertRaises(InvalidApplicationId, msg=f"Should reject '{val}'"):
                validate_application_id(val)


if __name__ == "__main__":
    unittest.main()
