from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from scripts.agent.render_wave_prompt import render
from scripts.agent.wave_common import task, task_ids, wave


ROOT = Path(__file__).resolve().parents[2]


class Wave03BootstrapTests(unittest.TestCase):
    def test_wave_three_manifest_and_lane_boundaries(self) -> None:
        manifest = wave("wave-03")
        self.assertEqual(manifest["wave_id"], "wave-03")
        self.assertEqual(manifest["integration_branch"], "integration/phase1-wave3")
        self.assertEqual(
            set(task_ids("wave-03")),
            {"acceptance", "agent-guidance", "application-builder", "generator", "integration"},
        )
        for lane in task_ids("wave-03"):
            value = task(lane, "wave-03")
            self.assertTrue(value["allowed_paths"], lane)
            self.assertTrue(value["required_tests"], lane)
            self.assertTrue(value["handoff_path"].startswith("docs/handoffs/wave-03/"))
            self.assertFalse(set(value["allowed_paths"]) & set(value["forbidden_paths"]))

    def test_wave_three_prompt_uses_selected_wave_and_lane(self) -> None:
        prompt = render("generator", "wave-03")
        self.assertIn("wave-03", prompt)
        self.assertIn("--wave wave-03 --task generator", prompt)
        self.assertIn("packages/servicefabric_application_generator", prompt)
        self.assertLess(len(prompt.split()), 300)

    def test_wave_three_json_records_are_valid(self) -> None:
        for path in (ROOT / "config/agent/waves/wave-03").glob("**/*.json"):
            json.loads(path.read_text(encoding="utf-8"))

    def test_wave_status_accepts_explicit_wave_option(self) -> None:
        result = subprocess.run(
            ["bash", "scripts/agents/wave_status.sh", "--wave", "wave-03"],
            cwd=ROOT,
            env={"PATH": "/usr/bin:/bin", "SF_AGENT_WORKTREES_ENV": str(ROOT / "missing.env")},
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Unknown argument: --wave", result.stderr)


if __name__ == "__main__":
    unittest.main()
