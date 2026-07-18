"""Bootstrap checks that do not implement specialist distillation behavior."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class WaveTenBootstrapTests(unittest.TestCase):
    def test_manifests_name_all_disjoint_lanes(self) -> None:
        manifest = json.loads((ROOT / "config/agents/wave-10/wave.yaml").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["specialist_lanes"]), 7)
        self.assertEqual(manifest["contractsStatus"], "frozen")
        self.assertEqual(set(manifest["worktree_env"]), set(manifest["lanes"]))
        for lane in manifest["lanes"]:
            self.assertTrue((ROOT / f"config/agents/wave-10/tasks/{lane}.json").is_file(), lane)
            self.assertTrue((ROOT / f"docs/handoffs/wave-10/{lane}.md").is_file(), lane)

    def test_contracts_are_contracts_only(self) -> None:
        package = ROOT / "packages/servicefabric_distillation_contracts/src/servicefabric_distillation_contracts"
        files = sorted(path.name for path in package.glob("*.py"))
        self.assertEqual(files, ["__init__.py", "contracts.py"])
        source = (package / "contracts.py").read_text(encoding="utf-8")
        for prohibited in ("subprocess", "os.system", "source_patch", "CapabilityRegistry("):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
