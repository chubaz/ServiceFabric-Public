from __future__ import annotations

import unittest

from pydantic import ValidationError

from servicefabric_contracts import ToolDeployment
from test_service_package import load_fixture


class ToolDeploymentTests(unittest.TestCase):
    def test_deployment_references_immutable_revision(self) -> None:
        deployment = ToolDeployment.model_validate(load_fixture("tool_deployment_math_calculate.json"))
        self.assertEqual(deployment.spec.tool_id, deployment.spec.revision_ref.tool_id)
        self.assertTrue(deployment.spec.revision_ref.content_digest.startswith("sha256:"))

    def test_weighted_traffic_must_total_one_hundred(self) -> None:
        payload = load_fixture("tool_deployment_math_calculate.json")
        primary = payload["spec"]["revision_ref"]
        secondary = {**primary, "revision": "1.1.0", "content_digest": "sha256:" + "d" * 64}
        payload["spec"]["traffic_policy"] = {"traffic_kind": "weighted", "targets": [{"revision_ref": primary, "percentage": 70}, {"revision_ref": secondary, "percentage": 20}]}
        with self.assertRaises(ValidationError):
            ToolDeployment.model_validate(payload)

    def test_deployment_rejects_live_health(self) -> None:
        payload = load_fixture("tool_deployment_math_calculate.json")
        payload["spec"]["availability"] = "available"
        with self.assertRaises(ValidationError):
            ToolDeployment.model_validate(payload)
