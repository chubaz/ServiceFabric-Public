from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "packages" / "servicefabric_contracts" / "src"),
    str(ROOT / "packages" / "servicefabric_builder"),
    str(ROOT / "packages" / "servicefabric_artifacts"),
    str(ROOT / "packages" / "servicefabric_capsules" / "src"),
    str(ROOT / "services"),
]

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from servicefabric_contracts import ApplicationBuildRequest
from servicefabric_capsules import CapsulePortfolio
from services.application_builder import ApplicationBuilderService


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


class CapsulePortfolioTests(unittest.TestCase):
    def test_example_capsule_resolves_against_artifact_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application_portfolio, store, artifact_digest = build_example_artifact(Path(temporary) / "store")
            portfolio = CapsulePortfolio(ROOT / "portfolio" / "capsules")
            resolution = portfolio.resolve("examples.hello-capsule", "1.0.0", application_portfolio, store)
            self.assertEqual(resolution.definition.spec.capsule_id, "examples.hello-capsule")
            self.assertEqual(resolution.revision.spec.revision_digest, "sha256:ed0f163932f90870080004c4cf5a1af3226b065696b7efc353e942f756e33cbf")
            self.assertEqual(resolution.artifact_digests, (artifact_digest,))

    def test_revision_digest_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application_portfolio, store, _ = build_example_artifact(Path(temporary) / "store")
            capsule_root = Path(temporary) / "capsules"
            shutil.copytree(ROOT / "portfolio" / "capsules", capsule_root)
            revision_path = capsule_root / "revisions" / "examples.hello-capsule-1.0.0.json"
            revision_path.write_text(
                revision_path.read_text(encoding="utf-8").replace(
                    "sha256:ed0f163932f90870080004c4cf5a1af3226b065696b7efc353e942f756e33cbf",
                    "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                ),
                encoding="utf-8",
            )
            portfolio = CapsulePortfolio(capsule_root)
            with self.assertRaises(ValueError):
                portfolio.resolve("examples.hello-capsule", "1.0.0", application_portfolio, store)
