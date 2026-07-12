from __future__ import annotations

import unittest

from pydantic import ValidationError

from servicefabric_contracts import ToolStatus
from test_service_package import load_fixture


class ToolStatusTests(unittest.TestCase):
    def test_status_fixture_is_observed_state(self) -> None:
        status = ToolStatus.model_validate(load_fixture("tool_status_math_calculate.json"))
        self.assertEqual(status.spec.availability, "available")
        self.assertIsNotNone(status.spec.conditions[0].observed_at.tzinfo)

    def test_status_rejects_contract_schemas(self) -> None:
        payload = load_fixture("tool_status_math_calculate.json")
        payload["spec"]["input_schema"] = {"schema_ref": "schema://invalid"}
        with self.assertRaises(ValidationError):
            ToolStatus.model_validate(payload)

    def test_condition_requires_timezone(self) -> None:
        payload = load_fixture("tool_status_math_calculate.json")
        payload["spec"]["conditions"][0]["observed_at"] = "2026-07-12T10:00:00"
        with self.assertRaises(ValidationError):
            ToolStatus.model_validate(payload)
