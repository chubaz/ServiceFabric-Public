import tempfile
import unittest
from pathlib import Path

from servicefabric_builder import ApplicationPortfolio, BuildError, BuildPolicy, StaticWebBuilder, validate_source


ROOT = Path(__file__).resolve().parents[2]


class StaticWebBuilderTests(unittest.TestCase):
    def setUp(self):
        self.portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
        self.revision = self.portfolio.revision("examples.hello-static", "1.0.0")
        self.source = validate_source(self.portfolio.source_root("hello-static-v1"), self.portfolio.verify_source(self.revision))

    def test_native_build_copies_normalized_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = StaticWebBuilder().build(self.revision, self.source, Path(temporary) / "output")
            self.assertEqual(output.entry_document, "index.html")
            self.assertEqual([record[0] for record in output.files], ["index.html", "styles.css"])
            self.assertTrue((output.output_root / "index.html").is_file())

    def test_output_budget_is_enforced(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(BuildError):
            StaticWebBuilder().build(self.revision, self.source, Path(temporary) / "output", BuildPolicy(maximum_output_bytes=1))
