from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from servicefabric_contracts import ApplicationBuildRequest, CapsuleAuthoringManifest
from servicefabric_capsules import CapsuleAuthoringService, CapsulePortfolio
from services.application_builder import ApplicationBuilderService


ROOT = Path(__file__).resolve().parents[2]


def build_example_artifact(store_root: Path):
    application_portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
    service = ApplicationBuilderService(application_portfolio, FileArtifactStore(store_root))
    request = ApplicationBuildRequest.model_validate(
        {
            "apiVersion": "servicefabric.ai/v1alpha1",
            "kind": "ApplicationBuildRequest",
            "metadata": {
                "id": "request.hello",
                "name": "Build hello",
                "description": "Build reviewed app",
                "owner_ref": {"kind": "team", "id": "platform"},
            },
            "spec": {
                "request_id": "request.hello",
                "application_id": "examples.hello-static",
                "revision": "1.0.0",
                "caller_context": {
                    "subject_ref": "builder-client",
                    "principal_type": "service",
                    "issuer": "servicefabric",
                    "authentication_strength": "workload",
                },
            },
        }
    )
    result = service.build_application(request)
    return application_portfolio, service.store, result.artifact_digest


class CapsuleAuthoringTests(unittest.TestCase):
    def test_authoring_publishes_and_reuses_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application_portfolio, store, _ = build_example_artifact(Path(temporary) / "store")
            capsule_root = Path(temporary) / "capsules"
            shutil.copytree(ROOT / "portfolio" / "capsules", capsule_root)
            revision_path = capsule_root / "revisions" / "examples.hello-capsule-1.0.0.json"
            revision_path.unlink()
            portfolio = CapsulePortfolio(capsule_root)
            service = CapsuleAuthoringService(
                portfolio,
                application_portfolio,
                store,
            )
            manifest = CapsuleAuthoringManifest.model_validate_json(
                (ROOT / "portfolio" / "capsules" / "authoring" / "examples.hello-capsule-1.0.0.json").read_text(encoding="utf-8")
            )
            first = service.author(manifest)
            self.assertEqual(first.status, "published")
            self.assertTrue(revision_path.is_file())
            second = service.author(manifest)
            self.assertEqual(second.status, "reused")
            self.assertEqual(first.revision_digest, second.revision_digest)

    def test_authoring_rejects_mismatched_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application_portfolio, store, _ = build_example_artifact(Path(temporary) / "store")
            capsule_root = Path(temporary) / "capsules"
            shutil.copytree(ROOT / "portfolio" / "capsules", capsule_root)
            portfolio = CapsulePortfolio(capsule_root)
            service = CapsuleAuthoringService(portfolio, application_portfolio, store)
            payload = json.loads((ROOT / "portfolio" / "capsules" / "authoring" / "examples.hello-capsule-1.0.0.json").read_text(encoding="utf-8"))
            payload["spec"]["bindings"][0]["artifact_digest"] = "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            manifest = CapsuleAuthoringManifest.model_validate(payload)
            result = service.author(manifest)
            self.assertEqual(result.status, "unsafe")
            self.assertTrue(result.diagnostics)

