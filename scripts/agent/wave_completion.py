#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent.common import git, read_json
from scripts.agent.wave_common import (
    canonical_handoff_path,
    committed_readiness_path,
    integration_queue_path,
    task_ids,
    wave,
)


def is_ancestor(commit: str) -> bool:
    return git("merge-base", "--is-ancestor", commit, "HEAD").returncode == 0


def inspect(wave_id: str) -> dict[str, object]:
    diagnostics: list[dict[str, str]] = []
    w = wave(wave_id)
    specialist_lanes = tuple(str(item) for item in w.get("specialist_lanes", ()))

    for task_id in task_ids(wave_id):
        handoff = canonical_handoff_path(task_id, wave_id)
        if not handoff.is_file():
            diagnostics.append({"severity": "error", "code": "missing_handoff", "message": str(handoff)})

    readiness_path = committed_readiness_path(wave_id)
    queue_path = integration_queue_path(wave_id)
    if not readiness_path.is_file():
        diagnostics.append({"severity": "error", "code": "missing_readiness", "message": str(readiness_path)})
        readiness: dict[str, object] = {}
    else:
        readiness = read_json(str(readiness_path.relative_to(Path(__file__).resolve().parents[2])))

    if not queue_path.is_file():
        diagnostics.append({"severity": "error", "code": "missing_integration_queue", "message": str(queue_path)})
        queue: dict[str, object] = {}
    else:
        queue = read_json(str(queue_path.relative_to(Path(__file__).resolve().parents[2])))

    lanes = readiness.get("lanes", {}) if isinstance(readiness, dict) else {}
    if not isinstance(lanes, dict):
        diagnostics.append({"severity": "error", "code": "invalid_readiness", "message": "lanes must be an object"})
        lanes = {}

    base = str(w["base_commit"])
    specialist_lanes = tuple(lane for lane in task_ids(wave_id) if lane != "integration")
    for lane in specialist_lanes:
        record = lanes.get(lane)
        if not isinstance(record, dict):
            diagnostics.append({"severity": "error", "code": "missing_lane_readiness", "message": lane})
            continue
        if record.get("original_base_sha") != base:
            diagnostics.append({"severity": "error", "code": "base_mismatch", "message": lane})
        if record.get("final_state") != "integrated":
            diagnostics.append({"severity": "error", "code": "lane_not_integrated", "message": lane})
        if record.get("integration_decision") != "accepted":
            diagnostics.append({"severity": "error", "code": "lane_not_accepted", "message": lane})
        if record.get("focused_verification") != "passed":
            diagnostics.append({"severity": "error", "code": "focused_verification", "message": lane})
        for key in ("candidate_head", "accepted_commit", "integration_commit"):
            commit = str(record.get(key, ""))
            if not commit or not is_ancestor(commit):
                diagnostics.append({"severity": "error", "code": f"{key}_not_integrated", "message": f"{lane}:{commit}"})

    integration = readiness.get("integration", {}) if isinstance(readiness, dict) else {}
    if not isinstance(integration, dict):
        integration = {}
        diagnostics.append({"severity": "error", "code": "missing_integration_readiness", "message": "integration"})
    if readiness.get("contractsStatus") != "frozen" or integration.get("contracts_status") != "frozen":
        diagnostics.append({"severity": "error", "code": "contracts_not_frozen", "message": "contractsStatus"})
    if integration.get("wave_completion_status") != "complete":
        diagnostics.append({"severity": "error", "code": "wave_incomplete", "message": "wave_completion_status"})
    if integration.get("final_verification_status") != "passed":
        diagnostics.append({"severity": "error", "code": "verification_incomplete", "message": "final_verification_status"})

    if queue.get("overall") != "WAVE COMPLETE":
        diagnostics.append({"severity": "error", "code": "queue_incomplete", "message": "overall"})

    frozen_paths = [str(item) for item in w["frozen_contracts"]]
    for lane, record in (lanes.items() if isinstance(lanes, dict) else ()):
        if not isinstance(record, dict) or lane not in specialist_lanes:
            continue
        commit = str(record.get("integration_commit", ""))
        if not commit:
            continue
        result = git("diff", "--name-only", f"{commit}^1", commit)
        for path in result.stdout.splitlines():
            if any(path == frozen or path.startswith(frozen.rstrip("/") + "/") for frozen in frozen_paths):
                diagnostics.append({"severity": "error", "code": "frozen_contract_changed", "message": f"{lane}:{path}"})

    return {
        "diagnostics": diagnostics,
        "ok": not any(item["severity"] == "error" for item in diagnostics),
        "wave": wave_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default="wave-1")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    result = inspect(args.wave)
    if args.format == "json":
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"Wave completion {args.wave}: {'passed' if result['ok'] else 'blocked'} ({len(result['diagnostics'])} diagnostics)")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
