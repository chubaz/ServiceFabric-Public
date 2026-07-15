#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent.common import ROOT
from scripts.agent.wave_common import canonical_handoff_path, runtime_wave_id, task, wave


def render(task_id: str, wave_id: str = "wave-1") -> str:
    w = wave(wave_id)
    t = task(task_id, wave_id)
    preflight_args = f"--task {task_id}" if wave_id in {"wave-1", "wave-01"} else f"--wave {wave_id} --task {task_id}"
    required = "\n".join(f"- {item}" for item in t["required_context_files"])
    allowed = "\n".join(f"- {item}" for item in t["allowed_paths"])
    forbidden = "\n".join(f"- {item}" for item in t["forbidden_paths"])
    tests = "\n".join(f"- `{item}`" for item in t["required_tests"])
    handoff_path = canonical_handoff_path(task_id, wave_id).relative_to(ROOT)
    authority = "You are the integration authority. Accept, reject, or return candidate commits with recorded reasons." if task_id == "integration" else "Create focused candidate commits only after tests pass. Do not merge your branch."
    runtime_id = runtime_wave_id(wave_id)
    return f"""You are the ServiceFabric `{w["wave_id"]}` `{task_id}` specialist.

Repository: ServiceFabric
Wave: `{w["wave_id"]}`
Base commit: `{w["base_commit"]}`
Branch: `{t["branch"]}`
Worktree: `{t["worktree"]}`

Objective: {t["objective"]}

Start by reading AGENTS.md, the shared wave docs, and required context. Run:

```bash
python3 scripts/agent/wave_task_preflight.py --wave {wave_id} --task {task_id}
```

Allowed paths:
{allowed}

Forbidden paths:
{forbidden}

Required context:
{required}

Required tests before candidate commit:
{tests}

Write test evidence to `{w["local_run_dir"]}/{task_id}/tests.json` and the committed handoff to `{handoff_path}` using `{w["handoff_template"]}`. Runtime `.agent-runs/{runtime_id}/{task_id}/handoff.md` files are generated mirrors, not authoritative handoffs. {authority} Stop and escalate if frozen contracts or another lane must change.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--wave", default="wave-1")
    parser.add_argument("--output")
    args = parser.parse_args()
    text = render(args.task, args.wave)
    if args.output:
        output = (ROOT / args.output).resolve()
        if ROOT not in output.parents and output != ROOT:
            raise SystemExit("output path escapes repository")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(output.relative_to(ROOT))
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
