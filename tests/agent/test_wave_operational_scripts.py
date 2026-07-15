from __future__ import annotations

import os
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LANES = {
    "assembly": "feature/wave1-assembly",
    "resources": "feature/wave1-resources",
    "kits-blueprints": "feature/wave1-kits-blueprints",
    "testing": "feature/wave1-testing",
}


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(command, cwd=cwd, env=merged, capture_output=True, text=True)


class TempWaveRepository:
    def __enter__(self) -> "TempWaveRepository":
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        ignore = shutil.ignore_patterns(
            ".git",
            ".agent",
            ".agent-runs",
            ".pytest_cache",
            ".sf-agent-runtime",
            ".venv",
            "__pycache__",
            "codex/logs",
        )
        shutil.copytree(ROOT, self.root, ignore=ignore)
        run(["git", "init"], self.root)
        run(["git", "config", "user.email", "agent@example.test"], self.root)
        run(["git", "config", "user.name", "Agent Test"], self.root)
        run(["git", "checkout", "-b", "integration/phase1-wave1"], self.root)
        run(["git", "add", "."], self.root)
        commit = run(["git", "commit", "-m", "test bootstrap"], self.root)
        if commit.returncode:
            raise AssertionError(commit.stdout + commit.stderr)
        self.base = run(["git", "rev-parse", "HEAD"], self.root).stdout.strip()
        manifest_path = self.root / "config/agent/waves/wave-1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["base_commit"] = self.base
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        run(["git", "add", str(manifest_path.relative_to(self.root))], self.root)
        commit = run(["git", "commit", "-m", "test wave base"], self.root)
        if commit.returncode:
            raise AssertionError(commit.stdout + commit.stderr)
        self.bootstrap = run(["git", "rev-parse", "HEAD"], self.root).stdout.strip()
        self.paths = {
            "integration": self.root,
            "assembly": Path(self.tmp.name) / "assembly",
            "resources": Path(self.tmp.name) / "resources",
            "kits-blueprints": Path(self.tmp.name) / "kits-blueprints",
            "testing": Path(self.tmp.name) / "testing",
        }
        for lane, branch in LANES.items():
            result = run(["git", "worktree", "add", "-b", branch, str(self.paths[lane]), self.bootstrap], self.root)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
        self.env_file = self.root / ".agent-worktrees.env"
        self.state_base = Path(self.tmp.name) / "state"
        self.env_file.write_text(
            "\n".join(
                [
                    'SF_WAVE_ID="wave-01"',
                    f'SF_STATE_BASE="{self.state_base}"',
                    f'SF_WT_INTEGRATION="{self.paths["integration"]}"',
                    f'SF_WT_ASSEMBLY="{self.paths["assembly"]}"',
                    f'SF_WT_RESOURCES="{self.paths["resources"]}"',
                    f'SF_WT_KITS_BLUEPRINTS="{self.paths["kits-blueprints"]}"',
                    f'SF_WT_TESTING="{self.paths["testing"]}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.env = {
            "SF_AGENT_WORKTREES_ENV": str(self.env_file),
            "SF_AGENT_WAVE_BASE_OVERRIDE": self.base,
            "SF_AGENT_SKIP_VENV": "1",
        }
        return self

    def __exit__(self, *exc: object) -> None:
        self.tmp.cleanup()

    def finalize(self, *extra: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = dict(self.env)
        if env:
            merged.update(env)
        return run(
            [
                "scripts/agents/finalize_existing_worktrees.sh",
                "--bootstrap-sha",
                self.bootstrap,
                *extra,
            ],
            self.root,
            merged,
        )


class WaveOperationalScriptTests(unittest.TestCase):
    def test_runtime_initializer_installs_locked_contracts_dependencies(self) -> None:
        content = (ROOT / "scripts/agents/init_worktree_runtime.sh").read_text(encoding="utf-8")
        self.assertIn('CONTRACTS="$WORKTREE/packages/servicefabric_contracts"', content)
        self.assertIn('"$CONTRACTS/requirements/test.lock"', content)
        self.assertIn('pip install --disable-pip-version-check --no-build-isolation --no-deps "$CONTRACTS"', content)

    def test_runtime_initializer_accepts_four_positional_arguments_for_both_waves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for wave_id, lane in (("wave-01", "assembly"), ("wave-02", "supervisor")):
                worktree = root / wave_id / "worktree"
                state = root / wave_id / "state"
                worktree.mkdir(parents=True)
                result = run(
                    [
                        "scripts/agents/init_worktree_runtime.sh",
                        lane,
                        str(worktree),
                        str(state),
                        wave_id,
                    ],
                    ROOT,
                    {
                        "SF_AGENT_SKIP_VENV": "1",
                        "SF_AGENT_WORKTREES_ENV": "/tmp/wave-worktrees.env",
                    },
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                runtime = worktree / ".agent-runtime.env"
                self.assertTrue(runtime.is_file())
                content = runtime.read_text(encoding="utf-8")
                self.assertIn(f'SF_AGENT_LANE="{lane}"', content)
                self.assertIn(f'SF_AGENT_WAVE_ID="{wave_id}"', content)
                self.assertIn("SF_AGENT_WORKTREES_ENV=/tmp/wave-worktrees.env", content)

    def test_wave_02_options_are_accepted_by_operational_scripts(self) -> None:
        env = {"SF_AGENT_WORKTREES_ENV": "/tmp/servicefabric-missing-wave-02.env"}
        for command in (
            ["scripts/agents/finalize_existing_worktrees.sh", "--wave", "wave-02", "--bootstrap-sha", "HEAD", "--dry-run"],
            ["scripts/agents/wave_status.sh", "--wave", "wave-02"],
            ["scripts/agents/launch_lane.sh", "--wave", "wave-02", "supervisor", "--interactive"],
        ):
            result = run(command, ROOT, env)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Unknown argument", result.stderr)
            self.assertIn("Missing worktree configuration", result.stderr)

    def test_missing_worktree_configuration_fails(self) -> None:
        result = run(
            ["scripts/agents/wave_status.sh"],
            ROOT,
            {"SF_AGENT_WORKTREES_ENV": "/tmp/servicefabric-missing-worktrees.env"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing worktree configuration", result.stderr)

    def test_invalid_worktree_path_fails(self) -> None:
        with TempWaveRepository() as repo:
            content = repo.env_file.read_text(encoding="utf-8")
            content = content.replace(
                f'SF_WT_ASSEMBLY="{repo.paths["assembly"]}"',
                f'SF_WT_ASSEMBLY="{repo.root.parent / "missing-assembly"}"',
            )
            repo.env_file.write_text(content, encoding="utf-8")
            result = repo.finalize("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid Git worktree", result.stderr)

    def test_dirty_worktree_fails(self) -> None:
        with TempWaveRepository() as repo:
            (repo.paths["assembly"] / "README.md").write_text("dirty\n", encoding="utf-8")
            result = repo.finalize("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("assembly: worktree is dirty", result.stderr)

    def test_detached_head_fails(self) -> None:
        with TempWaveRepository() as repo:
            run(["git", "checkout", "--detach", "HEAD"], repo.paths["assembly"])
            result = repo.finalize("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("detached HEAD", result.stderr)

    def test_base_mismatch_fails(self) -> None:
        with TempWaveRepository() as repo:
            path = repo.paths["assembly"]
            run(["git", "checkout", "--orphan", "disconnected"], path)
            (path / "orphan.txt").write_text("orphan\n", encoding="utf-8")
            run(["git", "add", "orphan.txt"], path)
            run(["git", "commit", "-m", "orphan"], path)
            run(["git", "branch", "-M", "feature/wave1-assembly"], path)
            result = repo.finalize("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not descend from wave-01 base", result.stderr)

    def test_specialist_branch_with_unexpected_commits_fails(self) -> None:
        with TempWaveRepository() as repo:
            path = repo.paths["assembly"]
            (path / "candidate.txt").write_text("candidate\n", encoding="utf-8")
            run(["git", "add", "candidate.txt"], path)
            run(["git", "commit", "-m", "feat(assembly): candidate"], path)
            result = repo.finalize("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected commits", result.stderr)

    def test_failed_runtime_initialization_stops(self) -> None:
        with TempWaveRepository() as repo:
            result = repo.finalize(env={"SF_AGENT_FAIL_RUNTIME_INIT": "assembly"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Runtime initialization forced to fail", result.stderr)

    def test_failed_preflight_stops(self) -> None:
        with TempWaveRepository() as repo:
            result = repo.finalize(env={"SF_AGENT_FAIL_PREFLIGHT": "assembly"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preflight forced to fail", result.stderr)

    def test_successful_dry_run_is_non_destructive(self) -> None:
        with TempWaveRepository() as repo:
            result = repo.finalize("--dry-run")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("DRY-RUN", result.stdout)
            self.assertNotIn("reset", result.stdout)
            self.assertNotIn("rebase", result.stdout)
            self.assertNotIn("clean -fd", result.stdout)
            self.assertFalse(repo.state_base.exists())

    def test_successful_prompt_rendering_and_idempotent_second_execution(self) -> None:
        with TempWaveRepository() as repo:
            first = repo.finalize()
            second = repo.finalize()
            status = run(["scripts/agents/wave_status.sh"], repo.root, repo.env)
            prompt = repo.paths["assembly"] / ".agent-runs/wave-01/assembly/prompt.md"
            readiness = repo.paths["assembly"] / ".agent-runs/wave-01/assembly/readiness.json"
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            self.assertIn("EXPECTED", status.stdout)
            self.assertIn("QUEUE", status.stdout)
            self.assertIn("OVERALL: READY FOR INTEGRATION AGENT", status.stdout)
            self.assertTrue(prompt.is_file())
            self.assertTrue(readiness.is_file())


if __name__ == "__main__":
    unittest.main()
