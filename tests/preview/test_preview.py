import http.client
import tempfile
import unittest
from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from services.application_builder import ApplicationBuilderService, PreviewServer
from tests.applications.test_service import request


ROOT = Path(__file__).resolve().parents[2]


class PreviewTests(unittest.TestCase):
    def test_loopback_preview_is_read_only_and_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = FileArtifactStore(Path(temporary) / "store")
            service = ApplicationBuilderService(ApplicationPortfolio(ROOT / "portfolio" / "applications"), store)
            result = service.build_application(request())
            with PreviewServer(store, result.artifact_digest) as preview:
                self.assertEqual(preview.address[0], "127.0.0.1")
                connection = http.client.HTTPConnection(*preview.address, timeout=2)
                connection.request("GET", "/")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
                response.read()
                connection.request("GET", "/../manifest.json")
                self.assertEqual(connection.getresponse().status, 404)
                connection.close()
