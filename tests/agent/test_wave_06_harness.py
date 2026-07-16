from __future__ import annotations

import unittest

from scripts.agent.wave_common import task, task_ids, wave


class Wave06HarnessTests(unittest.TestCase):
    def test_manifest_binds_projection_lanes_to_the_wave_six_integration_branch(self) -> None:
        manifest = wave("wave-06")

        self.assertEqual(manifest["integration_branch"], "integration/phase2-wave6")
        self.assertEqual(
            task_ids("wave-06"),
            ["acceptance", "integration", "mcp-projection", "rest-projection", "sdk-agent-projection"],
        )

    def test_projection_lanes_have_disjoint_owned_paths_and_bounded_suites(self) -> None:
        projection_lanes = ("mcp-projection", "rest-projection", "sdk-agent-projection")
        owned = [set(task(lane, "wave-06")["allowed_paths"]) for lane in projection_lanes]

        self.assertFalse(owned[0] & owned[1])
        self.assertFalse(owned[0] & owned[2])
        self.assertFalse(owned[1] & owned[2])
        self.assertTrue(all(task(lane, "wave-06")["focused_test_limit"] == 3 for lane in projection_lanes))
        self.assertEqual(task("acceptance", "wave-06")["focused_test_limit"], 1)


if __name__ == "__main__":
    unittest.main()
