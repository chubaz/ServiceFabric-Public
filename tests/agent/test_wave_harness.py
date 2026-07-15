from __future__ import annotations

import unittest

from scripts.agent.render_wave_prompt import render
from scripts.agent.wave_common import ROOT, task, task_ids, wave


class WaveHarnessTests(unittest.TestCase):
    def test_wave_manifest_records_required_bootstrap_fields(self) -> None:
        value = wave("wave-1")
        self.assertEqual(value["wave_id"], "wave-1")
        self.assertEqual(value["base_commit"], "5606a0556a3bb822e0168e59c4de421ccb963860")
        self.assertEqual(value["integration_branch"], "integration/phase1-wave1")
        self.assertEqual(
            set(value["specialist_branches"]),
            {"assembly", "resources", "kits-blueprints", "testing", "integration"},
        )
        self.assertIn("make verify-current", value["verification_gates"])
        self.assertEqual(value["canonical_handoff_dir"], "docs/handoffs/wave-01")
        self.assertEqual(
            value["canonical_handoffs"]["assembly"],
            "docs/handoffs/wave-01/assembly.md",
        )

    def test_task_manifests_are_structured_and_bounded(self) -> None:
        for task_id in task_ids("wave-1"):
            value = task(task_id, "wave-1")
            self.assertTrue(value["allowed_paths"], task_id)
            self.assertTrue(value["forbidden_paths"], task_id)
            self.assertTrue(value["required_context_files"], task_id)
            self.assertTrue(value["required_tests"], task_id)
            self.assertTrue(value["handoff_path"].startswith("docs/handoffs/wave-01/"), task_id)
            self.assertFalse(set(value["allowed_paths"]) & set(value["forbidden_paths"]), task_id)

    def test_specialists_cannot_modify_shared_controls(self) -> None:
        shared = {"Makefile", ".github", "clients/python", "schemas", "config/agent"}
        for task_id in {"assembly", "resources", "kits-blueprints", "testing"}:
            value = task(task_id, "wave-1")
            self.assertFalse(shared & set(value["allowed_paths"]), task_id)

    def test_prompt_renderer_is_concise_and_lane_specific(self) -> None:
        prompt = render("assembly", "wave-1")
        self.assertIn("feature/wave1-assembly", prompt)
        self.assertIn("wave_task_preflight.py --wave wave-1 --task assembly", prompt)
        self.assertIn("packages/servicefabric_application_assembly", prompt)
        self.assertIn("docs/handoffs/wave-01/assembly.md", prompt)
        self.assertLess(len(prompt.split()), 300)

    def test_handoff_template_is_versioned(self) -> None:
        path = ROOT / "docs/workplans/handoffs/wave-1/task-handoff-v1.md"
        self.assertTrue(path.is_file())
        self.assertIn("Wave-1 Task Handoff v1", path.read_text(encoding="utf-8"))

    def test_canonical_handoffs_are_committed(self) -> None:
        for name in ("assembly", "resources", "kits-blueprints", "testing", "integration"):
            path = ROOT / "docs" / "handoffs" / "wave-01" / f"{name}.md"
            self.assertTrue(path.is_file(), name)

    def test_wave_02_manifests_and_prompts_are_lane_specific(self) -> None:
        value = wave("wave-02")
        self.assertEqual(value["base_commit"], "715de644eff2ee003469f14d574c4b70706bc70a")
        self.assertEqual(value["integration_branch"], "integration/phase1-wave2")
        self.assertEqual(
            task_ids("wave-02"),
            ["integration", "kit-execution", "reference-app", "runtime-bindings", "supervisor"],
        )
        for task_id in task_ids("wave-02"):
            value = task(task_id, "wave-02")
            self.assertTrue(value["handoff_path"].startswith("docs/handoffs/wave-02/"), task_id)
            self.assertTrue((ROOT / value["handoff_path"]).is_file(), task_id)
        prompt = render("supervisor", "wave-02")
        self.assertIn("agent/w2-supervisor", prompt)
        self.assertIn("--wave wave-02 --task supervisor", prompt)
        self.assertIn("docs/handoffs/wave-02/supervisor.md", prompt)


if __name__ == "__main__":
    unittest.main()
