#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent.common import ROOT, git
from scripts.agent.wave_common import clean_tree, existing_branch, run_git, wave


def worktrees_by_branch() -> dict[str, Path]:
    result = git("worktree", "list", "--porcelain")
    entries: dict[str, Path] = {}
    current_path: Path | None = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line.removeprefix("worktree ")).resolve()
        elif line.startswith("branch ") and current_path is not None:
            branch = line.removeprefix("branch refs/heads/")
            entries[branch] = current_path
    return entries


def bootstrap(wave_id: str = "wave-1", dry_run: bool = False) -> list[str]:
    w = wave(wave_id)
    base = str(w["base_commit"])
    head = git("rev-parse", "HEAD").stdout.strip()
    if git("cat-file", "-e", f"{base}^{{commit}}").returncode:
        raise SystemExit(f"wave base commit is not available: {base}")
    if git("merge-base", "--is-ancestor", base, "HEAD").returncode:
        raise SystemExit(f"wave base {base} is not an ancestor of HEAD")
    branch = git("branch", "--show-current").stdout.strip() or "detached"
    if branch != w["integration_branch"]:
        raise SystemExit(f"expected integration branch {w['integration_branch']}, found {branch}")
    if not clean_tree():
        raise SystemExit("working tree is not clean")

    existing_worktrees = worktrees_by_branch()
    existing_paths = set(existing_worktrees.values())
    planned: list[str] = []
    branches = w["specialist_branches"]
    worktrees = w["worktree_names"]
    for lane in sorted(branches):
        branch = branches[lane]
        path = (ROOT / worktrees[lane]).resolve()
        if existing_worktrees.get(branch) == path:
            planned.append(f"{branch} -> {path} (already present)")
            continue
        if existing_branch(branch):
            raise SystemExit(f"branch already exists: {branch}")
        if path.exists() or path in existing_paths:
            raise SystemExit(f"worktree path already exists: {path}")
        planned.append(f"{branch} -> {path}")

    for lane in sorted(branches):
        branch = branches[lane]
        path = (ROOT / worktrees[lane]).resolve()
        if existing_worktrees.get(branch) == path:
            continue
        run_git(["worktree", "add", "-b", branch, str(path), head], dry_run)
    return planned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default="wave-1")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for item in bootstrap(args.wave, args.dry_run):
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
