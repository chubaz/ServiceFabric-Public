import unittest
from pathlib import Path

from servicefabric_builder import ApplicationPortfolio


ROOT = Path(__file__).resolve().parents[2]


class ApplicationPortfolioTests(unittest.TestCase):
    def test_reviewed_example_resolves_and_verifies(self):
        portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
        definition = portfolio.definition("examples.hello-static")
        revision = portfolio.revision("examples.hello-static", "1.0.0")
        manifest = portfolio.verify_source(revision)
        self.assertEqual(definition.spec.application_id, revision.spec.application_id)
        self.assertEqual(len(manifest.files), 2)

    def test_resource_path_escape_is_rejected(self):
        portfolio = ApplicationPortfolio(ROOT / "portfolio" / "applications")
        with self.assertRaises(ValueError):
            portfolio.definition("../secret")
