#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent.common import git, safe_path
from scripts.agent.wave_common import clean_tree, current_branch, task, wave


def inspect(task_id: str, wave_id: str = "wave-1") -> dict[str, object]:
    w = wave(wave_id)
    t = task(task_id, wave_id)
    diagnostics: list[dict[str, str]] = []
    base = str(w["base_commit"])

    branch = current_branch()
    if branch != t["branch"]:
        diagnostics.append({"severity": "error", "code": "branch", "message": f"expected {t['branch']}, found {branch}"})
    if git("merge-base", "--is-ancestor", base, "HEAD").returncode:
        diagnostics.append({"severity": "error", "code": "base_ancestry", "message": f"{base} is not an ancestor of HEAD"})
    if not clean_tree():
        diagnostics.append({"severity": "error", "code": "dirty_tree", "message": "working tree must be clean before task work"})

    for path in t["required_context_files"]:
        if not safe_path(path).exists():
            diagnostics.append({"severity": "error", "code": "missing_context", "message": path})
    for path in t["allowed_paths"] + t["forbidden_paths"]:
        safe_path(path)

    return {
        "branch": branch,
        "diagnostics": diagnostics,
        "ok": not any(item["severity"] == "error" for item in diagnostics),
        "task": task_id,
        "wave": wave_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--wave", default="wave-1")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    result = inspect(args.task, args.wave)
    if args.format == "json":
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"Wave task preflight {args.task}: {'passed' if result['ok'] else 'blocked'} ({len(result['diagnostics'])} diagnostics)")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
