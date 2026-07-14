from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class WaveRolloverScriptTests(unittest.TestCase):
    def test_close_wave_requires_a_wave_argument(self) -> None:
        result = subprocess.run(["bash", "scripts/agents/close_wave.sh"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--wave is required", result.stderr)

    def test_start_next_wave_rejects_missing_base(self) -> None:
        result = subprocess.run(
            ["bash", "scripts/agents/start_next_wave.sh", "--wave", "wave-03", "--base", "refs/heads/does-not-exist", "--dry-run"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("base ref does not exist", result.stderr)

    def test_rollover_scripts_keep_destructive_operations_out(self) -> None:
        for name in ("close_wave.sh", "start_next_wave.sh"):
            content = (ROOT / "scripts/agents" / name).read_text(encoding="utf-8")
            self.assertNotIn("reset --hard", content)
            self.assertNotIn("push --force", content)
            self.assertNotIn(" worktree remove", content)
            self.assertNotIn(" merge ", content)

    def test_transition_document_records_manual_merge_boundary(self) -> None:
        content = (ROOT / "docs/workplans/parallel/template/transition.md").read_text(encoding="utf-8")
        self.assertIn("Create and merge the pull request manually", content)
        self.assertIn("Fetch `origin/main`", content)


if __name__ == "__main__":
    unittest.main()
