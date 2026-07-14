from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.agent.common import ROOT, git, read_json, safe_path


WAVE_DIR = "config/agent/waves"


def wave(wave_id: str) -> dict[str, object]:
    return read_json(f"{WAVE_DIR}/{wave_id}.json")


def task(task_id: str, wave_id: str = "wave-1") -> dict[str, object]:
    return read_json(f"{WAVE_DIR}/{wave_id}/tasks/{task_id}.json")


def task_ids(wave_id: str = "wave-1") -> list[str]:
    directory = safe_path(f"{WAVE_DIR}/{wave_id}/tasks")
    return sorted(path.stem for path in directory.glob("*.json"))


def current_branch() -> str:
    return git("branch", "--show-current").stdout.strip() or "detached"


def clean_tree() -> bool:
    return not git("status", "--porcelain").stdout.strip()


def changed_files(base: str) -> list[str]:
    return git("diff", "--name-only", f"{base}...HEAD").stdout.splitlines()


def commits_since(base: str) -> list[tuple[str, str]]:
    result = git("log", "--format=%H%x00%s", f"{base}..HEAD")
    commits: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        commit, _, subject = line.partition("\0")
        if commit:
            commits.append((commit, subject))
    return commits


def path_matches(path: str, patterns: list[str]) -> bool:
    normalized = path.rstrip("/")
    for pattern in patterns:
        item = pattern.rstrip("/")
        if normalized == item or normalized.startswith(item + "/"):
            return True
    return False


def existing_branch(name: str) -> bool:
    return git("show-ref", "--verify", "--quiet", f"refs/heads/{name}").returncode == 0


def worktree_paths() -> set[Path]:
    result = git("worktree", "list", "--porcelain")
    paths: set[Path] = set()
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            paths.add(Path(line.removeprefix("worktree ")).resolve())
    return paths


def run_git(args: list[str], dry_run: bool) -> subprocess.CompletedProcess[str] | None:
    if dry_run:
        print("git " + " ".join(args))
        return None
    result = git(*args)
    if result.returncode:
        raise SystemExit(result.stderr or result.stdout)
    return result


def read_test_log(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("commands"), list):
        raise ValueError("test log must contain a commands array")
    return data
