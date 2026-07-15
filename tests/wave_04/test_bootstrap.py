from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.agent.render_wave_prompt import render
from scripts.agent.wave_common import task, task_ids, wave


ROOT = Path(__file__).resolve().parents[2]


class Wave04BootstrapTests(unittest.TestCase):
    def test_manifest_and_lane_boundaries(self) -> None:
        manifest = wave("wave-04")
        self.assertEqual(manifest["wave_id"], "wave-04")
        self.assertEqual(manifest["integration_branch"], "integration/phase2-wave4")
        self.assertEqual(
            set(task_ids("wave-04")),
            {"integration", "operation-model", "capability-model", "capability-registry", "capability-authoring"},
        )
        for lane in task_ids("wave-04"):
            value = task(lane, "wave-04")
            self.assertTrue(value["allowed_paths"], lane)
            self.assertTrue(value["required_tests"], lane)
            self.assertTrue(value["handoff_path"].startswith("docs/handoffs/wave-04/"))
            self.assertFalse(set(value["allowed_paths"]) & set(value["forbidden_paths"]))

    def test_prompt_is_wave_and_lane_specific(self) -> None:
        prompt = render("capability-authoring", "wave-04")
        self.assertIn("wave-04", prompt)
        self.assertIn("--wave wave-04 --task capability-authoring", prompt)
        self.assertIn("examples/research-notes", prompt)
        self.assertLess(len(prompt.split()), 350)

    def test_bootstrap_json_records_are_valid(self) -> None:
        for path in (ROOT / "config/agent/waves/wave-04").glob("**/*.json"):
            json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
