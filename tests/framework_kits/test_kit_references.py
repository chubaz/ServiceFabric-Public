"""Unit tests for parsed and validated framework kit references."""

from __future__ import annotations

import unittest

from servicefabric_framework_kits import parse_kit_reference, InvalidKitReference


class TestKitReferences(unittest.TestCase):
    def test_parse_valid_kit_references(self) -> None:
        ref_str = (
            "fastapi-service @ServiceFabric/portfolio/applications/"
            "revisions/examples.hello-static-1.0.0.json"
        )
        ref = parse_kit_reference(ref_str)
        self.assertEqual(ref.kit_id, "fastapi-service")
        self.assertEqual(ref.version, "1.0.0")

    def test_parse_invalid_kit_references(self) -> None:
        invalid_refs = [
            "fastapi-service",
            "fastapi-service@1.0.0",
            "fastapi-service @ServiceFabric/no-version.json",
            "invalid_id @ServiceFabric/examples.hello-static-1.0.0.json",
            "",
        ]
        for val in invalid_refs:
            with self.assertRaises(InvalidKitReference, msg=f"Should reject '{val}'"):
                parse_kit_reference(val)


if __name__ == "__main__":
    unittest.main()
