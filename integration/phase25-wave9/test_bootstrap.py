"""Bootstrap checks that do not implement any specialist factory lane."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class WaveNineBootstrapTests(unittest.TestCase):
    def test_promoted_manifests_name_all_factory_lanes(self) -> None:
        manifest = (ROOT / "config/agents/wave-09/wave.yaml").read_text(encoding="utf-8")
        for lane in (
            "technology-profile", "blueprint-compiler", "factory-lifecycle",
            "repository-bootstrap", "candidate-review", "application-integration",
            "evaluation", "integration",
        ):
            self.assertIn(lane, manifest)

    def test_no_promoted_manifest_references_draft_paths(self) -> None:
        for manifest in (ROOT / "config/agents/wave-09").rglob("*.yaml"):
            self.assertNotIn("wave-09-draft", manifest.read_text(encoding="utf-8"), manifest)
