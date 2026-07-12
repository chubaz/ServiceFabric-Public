from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from servicefabric_contracts import (
    CapsuleAuthoringManifest,
    CapsuleDefinition,
    CapsuleHostPolicy,
    CapsuleHostRequest,
    CapsuleHostResult,
    CapsuleHostSession,
    CapsuleRevision,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CapsuleContractTests(unittest.TestCase):
    def test_valid_capsule_contracts_round_trip(self) -> None:
        for model, fixture in (
            (CapsuleDefinition, "capsule_definition_hello.json"),
            (CapsuleRevision, "capsule_revision_hello_v1.json"),
            (CapsuleAuthoringManifest, "capsule_authoring_manifest_hello.json"),
            (CapsuleHostPolicy, "capsule_host_policy_loopback.json"),
            (CapsuleHostRequest, "capsule_host_request_hello.json"),
            (CapsuleHostSession, "capsule_host_session_hello.json"),
            (CapsuleHostResult, "capsule_host_result_hello_success.json"),
        ):
            with self.subTest(model=model.__name__):
                value = model.model_validate(load_fixture(fixture))
                self.assertEqual(value.kind, model.__name__)

    def test_definition_rejects_unknown_top_level_field(self) -> None:
        payload = load_fixture("capsule_definition_hello.json")
        payload["unknown"] = True
        with self.assertRaises(ValidationError):
            CapsuleDefinition.model_validate(payload)

    def test_revision_requires_entry_route_and_unique_bindings(self) -> None:
        payload = load_fixture("capsule_revision_hello_v1.json")
        payload["spec"]["entry_route"] = "/missing"
        with self.assertRaises(ValidationError):
            CapsuleRevision.model_validate(payload)
        payload = load_fixture("capsule_revision_hello_v1.json")
        payload["spec"]["artifact_bindings"].append(payload["spec"]["artifact_bindings"][0].copy())
        with self.assertRaises(ValidationError):
            CapsuleRevision.model_validate(payload)

    def test_route_normalization_rejects_traversal(self) -> None:
        payload = load_fixture("capsule_revision_hello_v1.json")
        payload["spec"]["routes"][0]["path"] = "/../secret"
        with self.assertRaises(ValidationError):
            CapsuleRevision.model_validate(payload)

    def test_bindings_must_not_overlap(self) -> None:
        payload = load_fixture("capsule_revision_hello_v1.json")
        payload["spec"]["artifact_bindings"].append(
            {
                **payload["spec"]["artifact_bindings"][0],
                "binding_id": "docs-static",
                "mount_path": "/docs",
            }
        )
        with self.assertRaises(ValidationError):
            CapsuleRevision.model_validate(payload)

    def test_host_request_rejects_privileged_port(self) -> None:
        payload = load_fixture("capsule_host_request_hello.json")
        payload["spec"]["requested_port"] = 80
        with self.assertRaises(ValidationError):
            CapsuleHostRequest.model_validate(payload)

    def test_host_result_validation(self) -> None:
        payload = load_fixture("capsule_host_result_hello_success.json")
        CapsuleHostResult.model_validate(payload)
        payload["spec"]["errors"] = [{"code": "SF-EXEC-CAPSULE_FAILED", "category": "execution", "message": "capsule failed", "retryable": False}]
        with self.assertRaises(ValidationError):
            CapsuleHostResult.model_validate(payload)

