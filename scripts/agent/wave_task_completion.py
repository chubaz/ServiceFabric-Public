#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent.common import git, safe_path
from scripts.agent.wave_common import (
    canonical_handoff_path,
    changed_files,
    clean_tree,
    commits_since,
    current_branch,
    path_matches,
    read_test_log,
    task,
    wave,
)


def comparison_base(task_id: str, integration_branch: str, frozen_base: str) -> str:
    result = git("merge-base", integration_branch, "HEAD")
    if result.returncode:
        return frozen_base
    return result.stdout.strip()


def inspect(task_id: str, wave_id: str, test_log: Path, handoff: Path) -> dict[str, object]:
    w = wave(wave_id)
    t = task(task_id, wave_id)
    base = str(w["base_commit"])
    diff_base = comparison_base(task_id, str(w["integration_branch"]), base)
    diagnostics: list[dict[str, str]] = []

    branch = current_branch()
    if branch != t["branch"]:
        diagnostics.append({"severity": "error", "code": "branch", "message": f"expected {t['branch']}, found {branch}"})
    if git("merge-base", "--is-ancestor", base, "HEAD").returncode:
        diagnostics.append({"severity": "error", "code": "base_ancestry", "message": f"{base} is not an ancestor of HEAD"})

    files = changed_files(diff_base)
    for path in files:
        if not path_matches(path, t["allowed_paths"]):
            diagnostics.append({"severity": "error", "code": "path_not_allowed", "message": path})
        if path_matches(path, t["forbidden_paths"]) or path_matches(path, w["frozen_contracts"]):
            diagnostics.append({"severity": "error", "code": "frozen_or_forbidden_path", "message": path})

    if not handoff.exists():
        diagnostics.append({"severity": "error", "code": "missing_handoff", "message": str(handoff)})

    if not test_log.exists():
        diagnostics.append({"severity": "error", "code": "missing_test_log", "message": str(test_log)})
    else:
        try:
            executed = {item["command"] for item in read_test_log(test_log)["commands"] if item.get("status") == "passed"}
            for command in t["required_tests"]:
                if command not in executed:
                    diagnostics.append({"severity": "error", "code": "required_test_missing", "message": command})
        except Exception as exc:
            diagnostics.append({"severity": "error", "code": "invalid_test_log", "message": str(exc)})

    policy = t["candidate_commit_policy"]
    prefixes = tuple(policy["allowed_prefixes"])
    for commit, subject in commits_since(diff_base):
        if subject.startswith("Merge ") and not policy["allow_merge_commits"]:
            diagnostics.append({"severity": "error", "code": "merge_commit", "message": commit})
        if not subject.startswith(prefixes):
            diagnostics.append({"severity": "error", "code": "commit_policy", "message": subject})

    if not clean_tree():
        diagnostics.append({"severity": "error", "code": "dirty_tree", "message": "working tree must be clean at completion"})

    return {
        "changed_files": files,
        "comparison_base": diff_base,
        "diagnostics": diagnostics,
        "ok": not any(item["severity"] == "error" for item in diagnostics),
        "task": task_id,
        "wave": wave_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--wave", default="wave-1")
    parser.add_argument("--test-log", required=True)
    parser.add_argument("--handoff")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    test_log = safe_path(args.test_log)
    handoff = safe_path(args.handoff) if args.handoff else canonical_handoff_path(args.task, args.wave)
    result = inspect(args.task, args.wave, test_log, handoff)
    if args.format == "json":
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"Wave task completion {args.task}: {'passed' if result['ok'] else 'blocked'} ({len(result['diagnostics'])} diagnostics)")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
