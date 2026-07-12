from __future__ import annotations

import unittest

from pydantic import ValidationError

from test_service_package import load_fixture
from servicefabric_contracts import ServicePackageDefinition


class InvariantTests(unittest.TestCase):
    def test_duplicate_entrypoints_are_rejected(self) -> None:
        payload = load_fixture("managed_http_capsule.json")
        payload["spec"]["entrypoints"].append(payload["spec"]["entrypoints"][0].copy())
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_invalid_semantic_version_is_rejected(self) -> None:
        payload = load_fixture("managed_http_capsule.json")
        payload["spec"]["package_version"] = "v1"
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_cli_mcp_must_be_machine_callable(self) -> None:
        payload = load_fixture("cli_financial_calculator.json")
        payload["spec"]["entrypoints"][0]["exposures"] = [{"kind": "mcp", "operation_refs": ["finance.calculate"]}]
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_none_hosting_is_the_only_empty_entrypoint_case(self) -> None:
        payload = load_fixture("managed_http_capsule.json")
        payload["spec"]["entrypoints"] = []
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_managed_static_requires_bundle_digest(self) -> None:
        payload = load_fixture("frontend_only_svelte.json")
        del payload["spec"]["artifact"]["digest"]
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_managed_graph_requires_revision_reference(self) -> None:
        payload = load_fixture("graph_backed_research.json")
        payload["spec"]["artifact"] = {"artifact_kind": "none"}
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_unknown_hosting_and_entrypoint_kinds_are_rejected(self) -> None:
        payload = load_fixture("managed_http_capsule.json")
        payload["spec"]["hosting"]["mode"] = "unknown"
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)
        payload = load_fixture("managed_http_capsule.json")
        payload["spec"]["entrypoints"][0]["kind"] = "unknown"
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)

    def test_secret_reference_rejects_literal_field(self) -> None:
        payload = load_fixture("external_http_provider.json")
        payload["spec"]["runtime_requirements"]["secret_refs"][0]["value"] = "literal-secret"
        with self.assertRaises(ValidationError):
            ServicePackageDefinition.model_validate(payload)
