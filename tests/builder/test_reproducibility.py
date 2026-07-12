import tempfile
import unittest
from pathlib import Path

from servicefabric_builder import ApplicationPortfolio, StaticWebBuilder, artifact_manifest, validate_source
from servicefabric_builder.source import ValidatedFile, ValidatedSourceBundle


ROOT = Path(__file__).resolve().parents[2]


class ReproducibilityTests(unittest.TestCase):
    def setUp(self):
        portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
        self.revision = portfolio.revision("examples.hello-static", "1.0.0")
        self.source = validate_source(portfolio.source_root("hello-static-v1"), portfolio.verify_source(self.revision))

    def build(self, source):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        builder = StaticWebBuilder()
        output = builder.build(self.revision, source, Path(temporary.name) / "output")
        return artifact_manifest(self.revision, output, builder)

    def test_different_workspaces_produce_same_identity(self):
        first = self.build(self.source)
        second = self.build(self.source)
        self.assertEqual(first.spec.artifact_digest, second.spec.artifact_digest)
        self.assertEqual(first.model_dump(mode="json"), second.model_dump(mode="json"))

    def test_one_byte_changes_artifact_identity(self):
        files = list(self.source.files)
        original = files[0]
        changed = original.content + b"x"
        import hashlib
        files[0] = ValidatedFile(original.path, original.media_type, changed, "sha256:" + hashlib.sha256(changed).hexdigest())
        altered = ValidatedSourceBundle(tuple(files), self.source.source_digest, self.source.total_size + 1)
        self.assertNotEqual(self.build(self.source).spec.artifact_digest, self.build(altered).spec.artifact_digest)
