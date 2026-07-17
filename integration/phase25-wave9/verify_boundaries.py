"""Verify the integration-owned Wave-9 contract freeze."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected an object: {path.relative_to(ROOT)}")
    return value


def paths_overlap(left: str, right: str) -> bool:
    left, right = left.rstrip("/"), right.rstrip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def main() -> int:
    manifest = load_json(ROOT / "config/agents/wave-09/wave.yaml")
    status = load_json(ROOT / "config/agent/waves/wave-09.json")
    if manifest.get("contractsStatus") != "frozen" or status.get("contractsStatus") != "frozen":
        raise ValueError("contractsStatus must remain frozen")
    if not (ROOT / "packages/servicefabric_application_factory_contracts").is_dir():
        raise ValueError("Wave-9 shared factory contracts are required")

    expected_boundaries = {
        "wave_03_generator_and_blueprint_apis": "authoritative",
        "wave_07_intent_task_plan_result_evidence_handoff_contracts": "authoritative",
        "wave_08_provider_runtime_and_execution_service": "authoritative",
        "technology_profiles": "governance-and-planning-inputs-only",
        "engineering_blueprint": "compiles-to-AgentRunPlan",
        "repository_bootstrap": "does-not-invoke-providers",
        "candidate_review": "read-only-no-code-integration",
        "application_integration": "accepted-exact-commit-shas-only",
        "unmet_requirement": "records-needs-without-modifying-ServiceFabric",
    }
    if manifest.get("boundary_freeze") != expected_boundaries:
        raise ValueError("Wave-9 boundary freeze changed")

    policies = manifest.get("operational_policies")
    expected_policies = {
        "contracts_freeze_required_before_specialists": True,
        "candidate_commits_allowed": True,
        "automatic_merger": False,
        "specialists_may_merge_or_pull_feature_branches": False,
        "lanes_may_merge_to_main": False,
        "candidate_review_read_only": True,
        "candidate_review_may_integrate_code": False,
        "repository_bootstrap_invokes_providers": False,
    }
    if policies != expected_policies:
        raise ValueError("Wave-9 operational policies changed")

    lanes = tuple(str(item) for item in manifest["specialist_lanes"])
    ceiling = manifest.get("specialist_test_command_ceiling")
    if not isinstance(ceiling, dict) or set(ceiling) != set(lanes):
        raise ValueError("Wave-9 must retain a focused-test ceiling for every specialist")
    owned: dict[str, tuple[str, ...]] = {}
    for lane in lanes:
        task = load_json(ROOT / "config/agents/wave-09/tasks" / f"{lane}.json")
        allowed = tuple(str(item) for item in task["allowed_paths"])
        required_tests = tuple(str(item) for item in task["required_tests"])
        limit = ceiling[lane]
        if not isinstance(limit, int) or limit < 1 or len(required_tests) > limit:
            raise ValueError(f"{lane} exceeds its focused-test ceiling")
        owned[lane] = allowed
    for index, lane in enumerate(lanes):
        for other in lanes[index + 1 :]:
            if any(paths_overlap(left, right) for left in owned[lane] for right in owned[other]):
                raise ValueError(f"specialist ownership overlaps: {lane} and {other}")

    print(f"Wave-9 boundaries: frozen; specialist paths: {len(lanes)} disjoint sets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
