"""Verify the integration-owned Wave-10 contract and ownership freeze."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path.relative_to(ROOT)}")
    return value


def paths_overlap(left: str, right: str) -> bool:
    left, right = left.rstrip("/"), right.rstrip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def main() -> int:
    manifest = load_json(ROOT / "config/agents/wave-10/wave.yaml")
    status = load_json(ROOT / "config/agent/waves/wave-10.json")
    if manifest.get("contractsStatus") != "frozen" or status.get("contractsStatus") != "frozen":
        raise ValueError("Wave-10 contracts must remain frozen")
    if manifest.get("base_commit") != "5d0add1332d71e79fc138aad42c025a3607d8aef":
        raise ValueError("Wave-10 approved base changed")
    if not (ROOT / "packages/servicefabric_distillation_contracts").is_dir():
        raise ValueError("shared distillation contracts are required")

    expected_boundaries = {
        "operation_definition": "authoritative",
        "capability_definition_and_registry": "authoritative",
        "application_blueprint_and_catalog": "authoritative",
        "application_factory_handoff": "authoritative",
        "unmet_requirement": "authoritative",
        "agent_plan_result_and_evidence": "authoritative",
        "wave_08_provider_events_and_usage": "authoritative",
        "wave_09_factory_lifecycle_store": "authoritative",
        "application_generator_and_factory": "authoritative",
        "blueprint_and_system_proposals": "records-only-no-source-modification",
    }
    if manifest.get("boundary_freeze") != expected_boundaries:
        raise ValueError("Wave-10 no-duplication boundary changed")

    specialist_lanes = tuple(str(item) for item in manifest["specialist_lanes"])
    ceilings = manifest.get("specialist_test_command_ceiling")
    if not isinstance(ceilings, dict) or set(ceilings) != set(specialist_lanes):
        raise ValueError("every specialist lane needs a test ceiling")
    if any(not isinstance(value, int) or value > 3 for value in ceilings.values()):
        raise ValueError("specialist test ceiling exceeds three")
    if ceilings.get("evaluation") != 1:
        raise ValueError("evaluation is limited to one journey")

    owned: list[tuple[str, str]] = []
    for lane in specialist_lanes:
        task = load_json(ROOT / f"config/agents/wave-10/tasks/{lane}.json")
        if task.get("branch") != f"agent/w10-{lane}":
            raise ValueError(f"unexpected branch for {lane}")
        allowed = task.get("allowed_paths")
        if not isinstance(allowed, list) or not allowed:
            raise ValueError(f"missing owned paths for {lane}")
        for path in (str(item) for item in allowed):
            for other_path, other_lane in owned:
                if paths_overlap(path, other_path):
                    raise ValueError(f"owned paths overlap: {lane} and {other_lane}")
            owned.append((path, lane))

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    target = makefile.split("verify-wave-10:", 1)[1].split("\nverify-wave-06:", 1)[0]
    for earlier in range(1, 10):
        if f"$(MAKE) verify-wave-{earlier:02d}" in target:
            raise ValueError("Wave-10 gate must not recursively invoke prior waves")
    required = (
        "tests/distillation_contracts", "tests/application_evidence",
        "tests/capability_distillation", "tests/technique_policies",
        "tests/engineering_distillation", "tests/evolution_proposals",
        "tests/release_readiness", "tests/wave_10",
        "tests.wave_09.test_application_factory", "tests.capability_registry.test_registry",
        "tests.release_readiness.test_doctor", "check_python_locks.py", "pip check",
        "compileall", "git diff --check",
    )
    missing = [item for item in required if item not in target]
    if missing:
        raise ValueError("Wave-10 gate is incomplete: " + ", ".join(missing))
    print("Wave-10 integration boundaries passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
