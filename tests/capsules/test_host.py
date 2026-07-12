from __future__ import annotations

import shutil
import tempfile
import sys
import unittest
from datetime import datetime, timedelta, timezone
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
from servicefabric_contracts import CapsuleHostRequest
from servicefabric_capsules import CapsuleHostService, CapsulePortfolio, LoopbackCapsuleHost


def load_request() -> CapsuleHostRequest:
    return CapsuleHostRequest.model_validate_json(
        (ROOT / "packages" / "servicefabric_contracts" / "tests" / "fixtures" / "capsule_host_request_hello.json").read_text(encoding="utf-8")
    )


def build_example_artifact(store_root: Path):
    application_portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
    from services.application_builder import ApplicationBuilderService
    from servicefabric_contracts import ApplicationBuildRequest

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


class CapsuleHostTests(unittest.TestCase):
    def test_loopback_host_serves_declared_assets_and_rejects_others(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application_portfolio, store, _ = build_example_artifact(Path(temporary) / "store")
            portfolio = CapsulePortfolio(ROOT / "portfolio" / "capsules")
            host = LoopbackCapsuleHost(portfolio, application_portfolio, store, load_request()).start()
            self.addCleanup(host.close)
            self.assertEqual(host.address[0], "127.0.0.1")
            response = host.dispatch("GET", "/")
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertTrue(response.body)
            response = host.dispatch("HEAD", "/styles.css")
            self.assertEqual(response.status, 200)
            self.assertEqual(response.body, b"")
            self.assertEqual(host.dispatch("GET", "/../manifest.json").status, 404)
            self.assertEqual(host.dispatch("POST", "/").status, 405)

    def test_request_limit_and_idle_expiration_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application_portfolio, store, _ = build_example_artifact(Path(temporary) / "store")
            capsule_root = Path(temporary) / "capsules"
            shutil.copytree(ROOT / "portfolio" / "capsules", capsule_root)
            policy = capsule_root / "host-policies" / "loopback-static.json"
            policy.write_text(policy.read_text(encoding="utf-8").replace('"maximum_requests": 100', '"maximum_requests": 1'), encoding="utf-8")
            portfolio = CapsulePortfolio(capsule_root)
            moments = [datetime(2026, 7, 12, 10, 0, tzinfo=timezone.utc)]

            def clock() -> datetime:
                return moments[0]

            host = LoopbackCapsuleHost(portfolio, application_portfolio, store, load_request(), clock=clock).start()
            self.addCleanup(host.close)
            self.assertEqual(host.dispatch("GET", "/").status, 200)
            self.assertEqual(host.dispatch("GET", "/styles.css").status, 503)
            moments[0] = moments[0] + timedelta(seconds=601)
            self.assertEqual(host.dispatch("GET", "/").status, 410)

    def test_close_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application_portfolio, store, _ = build_example_artifact(Path(temporary) / "store")
            portfolio = CapsulePortfolio(ROOT / "portfolio" / "capsules")
            host = CapsuleHostService(portfolio, application_portfolio, store).open_session(load_request())
            host.close()
            host.close()
