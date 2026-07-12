from __future__ import annotations

import json
import unittest
from pathlib import Path

from servicefabric_contracts import ServicePackageDefinition, ToolDefinition, ToolDeployment, ToolRevision, ToolStatus

RESOURCE_MODELS = {
    "ServicePackageDefinition": ServicePackageDefinition,
    "ToolDefinition": ToolDefinition,
    "ToolRevision": ToolRevision,
    "ToolDeployment": ToolDeployment,
    "ToolStatus": ToolStatus,
}


class FixtureTests(unittest.TestCase):
    def test_all_representative_fixtures_validate_and_serialize_deterministically(self) -> None:
        fixture_directory = Path(__file__).parent / "fixtures"
        for path in sorted(fixture_directory.glob("*.json")):
            with self.subTest(path=path.name):
                payload = json.loads(path.read_text(encoding="utf-8"))
                model = RESOURCE_MODELS[payload["kind"]].model_validate(payload)
                first = json.dumps(model.model_dump(by_alias=True, mode="json"), sort_keys=True, separators=(",", ":"))
                second = json.dumps(model.model_dump(by_alias=True, mode="json"), sort_keys=True, separators=(",", ":"))
                self.assertEqual(first, second)
