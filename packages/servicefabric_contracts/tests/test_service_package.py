from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from servicefabric_contracts import ServicePackageDefinition

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ServicePackageTests(unittest.TestCase):
    def test_frontend_only_package_is_valid(self) -> None:
        package = ServicePackageDefinition.model_validate(load_fixture("frontend_only_svelte.json"))
        self.assertEqual(package.spec.hosting.mode, "managed_static")
        self.assertFalse(package.spec.entrypoints[0].machine_callable)

    def test_external_service_cannot_claim_managed_resources(self) -> None:
        payload = load_fixture("external_http_provider.json")
        payload["spec"]["hosting"]["managed_resources"] = {"cpu_millicores": 1}
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_none_hosting_rejects_managed_artifact(self) -> None:
        payload = load_fixture("worker_only_reconciliation.json")
        payload["spec"]["hosting"] = {"mode": "none"}
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        payload = load_fixture("managed_http_capsule.json")
        payload["unknown"] = True
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)
