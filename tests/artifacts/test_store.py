import tempfile
import unittest
from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio, StaticWebBuilder, artifact_manifest, validate_source


ROOT = Path(__file__).resolve().parents[2]


class ArtifactStoreTests(unittest.TestCase):
    def build(self, temporary):
        portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
        revision = portfolio.revision("examples.hello-static", "1.0.0")
        source = validate_source(portfolio.source_root("hello-static-v1"), portfolio.verify_source(revision))
        builder = StaticWebBuilder()
        output = builder.build(revision, source, Path(temporary) / "output")
        return output, artifact_manifest(revision, output, builder)

    def test_atomic_publication_and_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build(temporary)
            store = FileArtifactStore(Path(temporary) / "store")
            self.assertEqual(store.put_artifact(manifest, output.output_root), manifest.spec.artifact_digest)
            self.assertTrue(store.verify_artifact(manifest.spec.artifact_digest).valid)
            self.assertEqual(store.open_file(manifest.spec.artifact_digest, "index.html")[:9], b"<!doctype")
            self.assertEqual(store.put_artifact(manifest, output.output_root), manifest.spec.artifact_digest)

    def test_tampering_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build(temporary)
            store = FileArtifactStore(Path(temporary) / "store")
            store.put_artifact(manifest, output.output_root)
            target = store._directory(manifest.spec.artifact_digest) / "files" / "index.html"
            target.chmod(0o644)
            target.write_bytes(b"tampered")
            self.assertFalse(store.verify_artifact(manifest.spec.artifact_digest).valid)

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = FileArtifactStore(Path(temporary) / "store")
            with self.assertRaises(ValueError):
                store.open_file("sha256:" + "a" * 64, "../secret")
