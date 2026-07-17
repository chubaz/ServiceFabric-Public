#!/usr/bin/python3
"""Deterministic local provider process used only by Wave-8 evaluation."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time


parser = argparse.ArgumentParser()
parser.add_argument("--provider", required=True)
parser.add_argument("--task", required=True)
parser.add_argument("--events", required=True)
parser.add_argument("--timeline", required=True)
parser.add_argument("--delay", required=True, type=float)
args = parser.parse_args()
os.setsid()
timeline = Path(args.timeline)


def record(phase: str, **extra: object) -> None:
    value = {
        "provider": args.provider,
        "task": args.task,
        "phase": phase,
        "time": time.monotonic(),
        "pid": os.getpid(),
        "pgid": os.getpgrp(),
        **extra,
    }
    with timeline.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


def terminate(_signum: int, _frame: object) -> None:
    record("terminated", status=143)
    raise SystemExit(143)


signal.signal(signal.SIGTERM, terminate)
record("start")
time.sleep(args.delay)
for line in Path(args.events).read_text(encoding="utf-8").splitlines():
    print(line, flush=True)
status = 1 if "failure" in Path(args.events).name else 0
record("finish", status=status)
sys.exit(status)
