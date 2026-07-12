import tempfile
import unittest
from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from servicefabric_contracts import ApplicationBuildRequest
from services.application_builder import ApplicationBuilderService


ROOT = Path(__file__).resolve().parents[2]


def request():
    return ApplicationBuildRequest.model_validate({
        "apiVersion": "servicefabric.ai/v1alpha1",
        "kind": "ApplicationBuildRequest",
        "metadata": {"id": "request.hello", "name": "Build hello", "description": "Build reviewed app", "owner_ref": {"kind": "team", "id": "platform"}},
        "spec": {
            "request_id": "request.hello",
            "application_id": "examples.hello-static",
            "revision": "1.0.0",
            "caller_context": {"subject_ref": "builder-client", "principal_type": "service", "issuer": "servicefabric", "authentication_strength": "workload"},
        },
    })


class ApplicationBuilderServiceTests(unittest.TestCase):
    def test_build_flows_through_service_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            service = ApplicationBuilderService(ApplicationPortfolio(ROOT / "portfolio" / "applications"), FileArtifactStore(Path(temporary) / "store"))
            result = service.build_application(request())
            self.assertEqual(result.status, "success")
            self.assertTrue(service.verify_artifact(result.artifact_digest).valid)
            self.assertEqual(service.list_applications(), ("examples.hello-static",))

    def test_errors_are_caller_safe(self):
        payload = request().model_dump(mode="json", by_alias=True)
        payload["spec"]["revision"] = "9.9.9"
        with tempfile.TemporaryDirectory() as temporary:
            service = ApplicationBuilderService(ApplicationPortfolio(ROOT / "portfolio" / "applications"), FileArtifactStore(Path(temporary) / "store"))
            result = service.build_application(ApplicationBuildRequest.model_validate(payload))
        self.assertEqual(result.status, "error")
        self.assertNotIn(str(ROOT), result.errors[0].message)
