from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.agent.render_wave_prompt import render
from scripts.agent.wave_common import (
    committed_readiness_path,
    integration_queue_path,
    task,
    task_ids,
    wave,
)


ROOT = Path(__file__).resolve().parents[2]


class Wave05BootstrapTests(unittest.TestCase):
    def test_manifest_and_lane_boundaries_are_complete(self) -> None:
        manifest = wave("wave-05")
        self.assertEqual(manifest["base_commit"], "53f53ca8a4a9a47887902b84a91bc27a812e9483")
        self.assertEqual(manifest["integration_branch"], "integration/phase2-wave5")
        self.assertEqual(
            set(task_ids("wave-05")),
            {"integration", "availability", "invocation", "http-adapter", "acceptance"},
        )
        for lane in task_ids("wave-05"):
            value = task(lane, "wave-05")
            self.assertTrue(value["allowed_paths"], lane)
            self.assertTrue(value["forbidden_paths"], lane)
            self.assertTrue(value["candidate_commit_policy"], lane)
            self.assertFalse(set(value["allowed_paths"]) & set(value["forbidden_paths"]), lane)
            self.assertTrue((ROOT / value["handoff_path"]).is_file(), lane)

    def test_specialist_limits_and_exclusions_are_recorded(self) -> None:
        self.assertEqual(task("availability", "wave-05")["focused_test_limit"], 4)
        self.assertEqual(task("invocation", "wave-05")["focused_test_limit"], 4)
        self.assertEqual(task("http-adapter", "wave-05")["focused_test_limit"], 3)
        self.assertEqual(task("acceptance", "wave-05")["focused_test_limit"], 2)
        frozen = set(wave("wave-05")["frozen_contracts"])
        self.assertIn("packages/servicefabric_capability_registry", frozen)
        self.assertIn("ToolDefinition", frozen)

    def test_prompts_are_lane_specific_and_bounded(self) -> None:
        for lane in task_ids("wave-05"):
            prompt = render(lane, "wave-05")
            self.assertIn(f"--wave wave-05 --task {lane}", prompt)
            self.assertIn(task(lane, "wave-05")["handoff_path"], prompt)
            self.assertLess(len(prompt.split()), 400)

    def test_readiness_queue_and_json_records_reflect_completed_wave(self) -> None:
        readiness = json.loads(committed_readiness_path("wave-05").read_text(encoding="utf-8"))
        queue = json.loads(integration_queue_path("wave-05").read_text(encoding="utf-8"))
        self.assertEqual(readiness["contractsStatus"], "frozen")
        self.assertEqual(queue["overall"], "WAVE COMPLETE")
        self.assertEqual(queue["lanes"]["integration"], "complete")
        for lane in ("availability", "invocation", "http-adapter", "acceptance"):
            self.assertEqual(queue["lanes"][lane], "accepted")
            self.assertEqual(readiness["lanes"][lane]["final_state"], "integrated")
        for path in (ROOT / "config/agent/waves/wave-05").glob("**/*.json"):
            json.loads(path.read_text(encoding="utf-8"))

    def test_wave_five_gate_is_focused(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        target = makefile.split("verify-wave-05:", 1)[1].split("\nverify-application-workspace:", 1)[0]
        for suite in (
            "tests/capability_runtime",
            "tests/capability_invocation",
            "tests/http_operation_adapter",
            "tests/wave_05",
        ):
            self.assertIn(suite, target)
        for earlier_wave in ("verify-wave-01", "verify-wave-02", "verify-wave-03", "verify-wave-04"):
            self.assertNotIn(f"$(MAKE) {earlier_wave}", target)


if __name__ == "__main__":
    unittest.main()
