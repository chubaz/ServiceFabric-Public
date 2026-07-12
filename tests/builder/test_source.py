import os
import tempfile
import unittest
from pathlib import Path

from servicefabric_builder.source import SourceValidationError, normalize_content, normalize_path, validate_source
from servicefabric_builder import ApplicationPortfolio


ROOT = Path(__file__).resolve().parents[2]


class SourceValidationTests(unittest.TestCase):
    def test_reviewed_source_validates_in_stable_order(self):
        portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
        revision = portfolio.revision("examples.hello-static", "1.0.0")
        source = validate_source(portfolio.source_root(revision.spec.source_bundle_ref), portfolio.verify_source(revision))
        self.assertEqual([item.path for item in source.files], ["index.html", "styles.css"])

    def test_unsafe_paths_are_rejected(self):
        for value in ("../x", "/etc/passwd", "C:/x", "a\\b", "a//b"):
            with self.subTest(value=value), self.assertRaises(SourceValidationError):
                normalize_path(value)

    def test_text_normalization_is_stable(self):
        self.assertEqual(normalize_content("text/plain", b"\xef\xbb\xbfhello\r\n"), b"hello\n")

    def test_symlink_is_rejected(self):
        portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
        revision = portfolio.revision("examples.hello-static", "1.0.0")
        manifest = portfolio.source_manifest(revision.spec.source_bundle_ref)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            os.symlink("/etc/passwd", root / "index.html")
            (root / "styles.css").write_bytes((portfolio.source_root("hello-static-v1") / "styles.css").read_bytes())
            with self.assertRaises(SourceValidationError):
                validate_source(root, manifest)
