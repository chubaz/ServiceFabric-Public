#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent.common import ROOT
from scripts.agent.wave_common import canonical_handoff_path, task_ids


def runtime_wave_id(wave_id: str) -> str:
    return "wave-01" if wave_id == "wave-1" else wave_id


def sync(task_id: str, worktree: Path, wave_id: str) -> Path:
    source = canonical_handoff_path(task_id, wave_id)
    if not source.is_file():
        raise FileNotFoundError(source)
    target = worktree / ".agent-runs" / runtime_wave_id(wave_id) / task_id / "handoff.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.read_bytes() != source.read_bytes():
        shutil.copyfile(source, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default="wave-1")
    parser.add_argument("--task")
    parser.add_argument("--worktree", default=".")
    args = parser.parse_args()

    worktree = (ROOT / args.worktree).resolve()
    tasks = [args.task] if args.task else task_ids(args.wave)
    for task_id in tasks:
        target = sync(task_id, worktree, args.wave)
        print(os.fspath(target.relative_to(worktree)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
