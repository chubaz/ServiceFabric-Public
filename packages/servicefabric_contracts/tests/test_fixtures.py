from __future__ import annotations

import json
import unittest
from pathlib import Path

from servicefabric_contracts import ServicePackageDefinition


class FixtureTests(unittest.TestCase):
    def test_all_representative_fixtures_validate_and_serialize_deterministically(self) -> None:
        fixture_directory = Path(__file__).parent / "fixtures"
        for path in sorted(fixture_directory.glob("*.json")):
            with self.subTest(path=path.name):
                model = ServicePackageDefinition.model_validate_json(path.read_text(encoding="utf-8"))
                first = json.dumps(model.model_dump(by_alias=True, mode="json"), sort_keys=True, separators=(",", ":"))
                second = json.dumps(model.model_dump(by_alias=True, mode="json"), sort_keys=True, separators=(",", ":"))
                self.assertEqual(first, second)
