#!/usr/bin/env python3
"""Verify the integration-owned Wave-7 contract freeze."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WAVE_DIR = ROOT / "config" / "agent" / "waves" / "wave-07"


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected an object: {path.relative_to(ROOT)}")
    return value


def paths_overlap(left: str, right: str) -> bool:
    left = left.rstrip("/")
    right = right.rstrip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def main() -> int:
    manifest = load_json(WAVE_DIR.with_suffix(".json"))
    readiness = load_json(WAVE_DIR / "readiness.json")
    lanes = tuple(str(item) for item in manifest["specialist_lanes"])
    if len(lanes) != 7:
        raise ValueError("Wave-7 must retain exactly seven specialist lanes")
    if readiness.get("contractsStatus") != "frozen":
        raise ValueError("contractsStatus must remain frozen")

    expected_boundaries = {
        "agentic_contracts": "data-and-protocols-only",
        "context": "builds-context-without-planning",
        "planner": "plans-without-persistence-or-execution",
        "run_store": "persists-without-scheduling",
        "orchestrator": "coordinates-without-model-invocation-or-file-editing",
        "harness": "executes-task-contracts-without-planning",
        "agent_tools": "public-servicefabric-boundaries-only",
        "capability_access": "delegates-through-CapabilityConsumerFacade",
        "arbitrary_shell_tool": False,
        "provider_adapters_owner": "wave-08",
    }
    if manifest.get("boundary_freeze") != expected_boundaries:
        raise ValueError("Wave-7 boundary freeze changed")

    ceiling = manifest.get("specialist_test_command_ceiling")
    if not isinstance(ceiling, int) or ceiling < 1:
        raise ValueError("specialist test-command ceiling must be a positive integer")
    owned: dict[str, tuple[str, ...]] = {}
    for lane in lanes:
        task = load_json(WAVE_DIR / "tasks" / f"{lane}.json")
        allowed = tuple(str(item) for item in task["allowed_paths"])
        required_tests = tuple(str(item) for item in task["required_tests"])
        if len(required_tests) > ceiling:
            raise ValueError(f"{lane} exceeds the focused-test ceiling of {ceiling}")
        owned[lane] = allowed

    for index, lane in enumerate(lanes):
        for other in lanes[index + 1 :]:
            if any(paths_overlap(left, right) for left in owned[lane] for right in owned[other]):
                raise ValueError(f"specialist ownership overlaps: {lane} and {other}")

    print(
        f"Wave-7 boundaries: frozen; specialist paths: {len(lanes)} disjoint sets; "
        f"focused-test ceiling: {ceiling}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
