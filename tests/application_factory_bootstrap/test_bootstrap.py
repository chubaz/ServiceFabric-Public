from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import servicefabric_application_factory_bootstrap as package

from servicefabric_application_factory_bootstrap import (
    BootstrapError,
    RepositoryBootstrap,
    WorktreeSpec,
)


class RepositoryBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        self._git("init", "--quiet")
        self._git("config", "user.email", "factory@example.invalid")
        self._git("config", "user.name", "Factory Test")
        (self.repository / "README.md").write_text("base\n", encoding="utf-8")
        self._git("add", "README.md")
        self._git("commit", "--quiet", "-m", "base")
        self.base = self._git("rev-parse", "HEAD").stdout.strip()
        self.bootstrap = RepositoryBootstrap(self.repository)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_creates_all_worktrees_from_the_resolved_base(self) -> None:
        self.assertEqual("servicefabric_application_factory_bootstrap", package.__name__)
        with patch.object(package.bootstrap.subprocess, "run", wraps=subprocess.run) as git_run:
            result = self.bootstrap.create_worktrees(
                base_commit="HEAD",
                integration=WorktreeSpec("integration/factory", self.root / "integration"),
                lanes=(
                    WorktreeSpec("agent/factory-one", self.root / "one"),
                    WorktreeSpec("agent/factory-two", self.root / "two"),
                ),
            )

        self.assertEqual(self.base, result.repository.base_commit)
        self.assertEqual(3, len(result.worktrees))
        for worktree in result.worktrees:
            self.assertTrue(worktree.path.is_dir())
            self.assertEqual(self.base, self._git_at(worktree.path, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual({"git"}, {call.args[0][0] for call in git_run.call_args_list})
        invoked_arguments = [argument for call in git_run.call_args_list for argument in call.args[0]]
        for forbidden in ("--force", "-f", "reset", "remove", "delete", "provider"):
            self.assertNotIn(forbidden, invoked_arguments)

    def test_refuses_existing_target_without_altering_it(self) -> None:
        target = self.root / "existing"
        target.mkdir()
        marker = target / "keep.txt"
        marker.write_text("keep", encoding="utf-8")

        with self.assertRaisesRegex(BootstrapError, "already exists"):
            self.bootstrap.create_worktrees(
                base_commit="HEAD",
                integration=WorktreeSpec("integration/factory", target),
                lanes=(),
            )

        self.assertEqual("keep", marker.read_text(encoding="utf-8"))
        self.assertEqual("", self._git("branch", "--list", "integration/factory").stdout)

    def test_refuses_duplicate_branch_before_creating_any_worktree(self) -> None:
        with self.assertRaisesRegex(BootstrapError, "distinct branch"):
            self.bootstrap.create_worktrees(
                base_commit="HEAD",
                integration=WorktreeSpec("agent/duplicate", self.root / "integration"),
                lanes=(WorktreeSpec("agent/duplicate", self.root / "lane"),),
            )

        self.assertFalse((self.root / "integration").exists())
        self.assertFalse((self.root / "lane").exists())

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self._git_at(self.repository, *args)

    @staticmethod
    def _git_at(directory: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=directory, check=True, capture_output=True, text=True
        )


if __name__ == "__main__":
    unittest.main()
