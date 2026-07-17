"""Repository bootstrap operations with explicit, non-destructive safeguards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Iterable


class BootstrapError(RuntimeError):
    """Raised when a repository cannot safely be prepared for candidate work."""


@dataclass(frozen=True)
class WorktreeSpec:
    """The branch and path owned by one candidate or integration lane."""

    branch: str
    path: Path

    def __post_init__(self) -> None:
        if not self.branch or self.branch.strip() != self.branch:
            raise ValueError("worktree branch must be a non-empty, trimmed name")


@dataclass(frozen=True)
class RepositoryState:
    """Validated local repository state, including the resolved immutable base."""

    root: Path
    base_commit: str


@dataclass(frozen=True)
class BootstrapResult:
    """Evidence of the worktrees created during one bootstrap operation."""

    repository: RepositoryState
    integration: WorktreeSpec
    lanes: tuple[WorktreeSpec, ...]

    @property
    def worktrees(self) -> tuple[WorktreeSpec, ...]:
        return (self.integration, *self.lanes)


class RepositoryBootstrap:
    """Create new Git worktrees without altering existing refs or worktrees.

    The class invokes only local Git commands.  It does not fetch, merge, reset,
    remove worktrees, or invoke application providers.
    """

    def __init__(self, repository: str | Path, *, git_binary: str = "git") -> None:
        self._repository = Path(repository).resolve()
        self._git_binary = git_binary

    def validate(self, base_commit: str) -> RepositoryState:
        """Confirm *base_commit* names a commit in this local working tree."""
        if not base_commit:
            raise ValueError("base_commit must be supplied")
        inside = self._git("rev-parse", "--is-inside-work-tree")
        if inside.stdout.strip() != "true":
            raise BootstrapError(f"{self._repository} is not a Git working tree")
        root = Path(self._git("rev-parse", "--show-toplevel").stdout.strip()).resolve()
        resolved = self._git("rev-parse", "--verify", f"{base_commit}^{{commit}}")
        return RepositoryState(root=root, base_commit=resolved.stdout.strip())

    def create_worktrees(
        self,
        *,
        base_commit: str,
        integration: WorktreeSpec,
        lanes: Iterable[WorktreeSpec],
    ) -> BootstrapResult:
        """Create the integration and candidate worktrees at one resolved base.

        Every target must be new and every branch name must be unused.  These
        checks make the operation additive: existing worktrees and refs are never
        overwritten or repointed.
        """
        repository = self.validate(base_commit)
        lane_specs = tuple(lanes)
        specs = (integration, *lane_specs)
        self._validate_specs(specs)
        for spec in specs:
            self._ensure_target_is_new(spec, repository.root)

        created: list[WorktreeSpec] = []
        try:
            for spec in specs:
                target = spec.path.resolve()
                self._git_at(
                    repository.root,
                    "worktree",
                    "add",
                    "--quiet",
                    "-b",
                    spec.branch,
                    str(target),
                    repository.base_commit,
                )
                head = self._git_at(target, "rev-parse", "HEAD").stdout.strip()
                if head != repository.base_commit:
                    raise BootstrapError(
                        f"worktree {target} was created at {head}, not {repository.base_commit}"
                    )
                created.append(WorktreeSpec(branch=spec.branch, path=target))
        except BootstrapError as error:
            created_paths = ", ".join(str(spec.path) for spec in created) or "none"
            raise BootstrapError(
                f"bootstrap stopped without cleanup; created worktrees: {created_paths}. {error}"
            ) from error

        return BootstrapResult(
            repository=repository,
            integration=created[0],
            lanes=tuple(created[1:]),
        )

    def _validate_specs(self, specs: tuple[WorktreeSpec, ...]) -> None:
        if not specs:
            raise ValueError("at least one worktree spec is required")
        branches = [spec.branch for spec in specs]
        paths = [spec.path.resolve() for spec in specs]
        if len(branches) != len(set(branches)):
            raise BootstrapError("each worktree must have a distinct branch")
        if len(paths) != len(set(paths)):
            raise BootstrapError("each worktree must have a distinct path")

    def _ensure_target_is_new(self, spec: WorktreeSpec, root: Path) -> None:
        target = spec.path.resolve()
        if target.exists():
            raise BootstrapError(f"worktree target already exists: {target}")
        if not target.parent.exists():
            raise BootstrapError(f"worktree parent does not exist: {target.parent}")
        ref = self._git_at(
            root,
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{spec.branch}",
            check=False,
        )
        if ref.returncode == 0:
            raise BootstrapError(f"branch already exists: {spec.branch}")
        if ref.returncode != 1:
            raise BootstrapError(f"could not inspect branch: {spec.branch}")

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self._git_at(self._repository, *args, check=check)

    def _git_at(
        self, directory: Path, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [self._git_binary, *args],
            cwd=directory,
            check=False,
            capture_output=True,
            text=True,
        )
        if check and completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown Git error"
            raise BootstrapError(f"git {' '.join(args)} failed: {detail}")
        return completed
