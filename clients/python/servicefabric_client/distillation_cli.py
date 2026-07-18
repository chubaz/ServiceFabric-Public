"""CLI adapter for the public Wave-10 distillation composition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from servicefabric_capability_model import CapabilityDefinition
from servicefabric_distillation_contracts import DistillationDecision, TechniquePolicyDefinition
from servicefabric_operation_model import OperationDefinition

from .distillation import DistillationInputs, DistillationService, ManifestSource


def _object(path: str | Path) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("distillation request must be a JSON object")
    return value


def load_inputs(run_id: str, path: str | Path) -> DistillationInputs:
    value = _object(path)
    sources = value.get("manifests", ())
    artifacts = value.get("artifacts", ())
    if not isinstance(sources, list) or not isinstance(artifacts, list):
        raise ValueError("manifests and artifacts must be arrays")
    return DistillationInputs(
        run_id=run_id,
        manifests=tuple(_manifest(item) for item in (*sources, *artifacts)),
        declared_operations=tuple(
            OperationDefinition.model_validate(item) for item in value.get("operations", ())
        ),
        declared_capabilities=tuple(
            CapabilityDefinition.model_validate(item) for item in value.get("capabilities", ())
        ),
        technique_policy_definitions=tuple(
            TechniquePolicyDefinition.model_validate(item)
            for item in value.get("technique_policies", ())
        ),
        blueprint_categories=_mapping(value.get("blueprint_categories", {})),
        system_scopes=_mapping(value.get("system_scopes", {})),
        engineering_pattern_version=(
            str(value["engineering_pattern_version"])
            if value.get("engineering_pattern_version") is not None
            else None
        ),
    )


def dispatch_distillation(args: Any, workspace: object) -> tuple[int, str, object]:
    service = DistillationService.for_current_environment(workspace)
    action = args.distillation_action
    if action == "decide":
        decision = DistillationDecision.model_validate(_object(args.decision))
        return 0, "distillation-decide", service.decide(decision)
    inputs = load_inputs(args.run_id, args.request)
    if action == "collect":
        return 0, "distillation-collect", service.collect(inputs).bundle
    if action == "analyze":
        return 0, "distillation-analyze", service.analyze(inputs)
    if action == "candidates":
        return 0, "distillation-candidates", {"candidates": service.candidates(inputs)}
    if action in {"publish", "report"}:
        return 0, f"distillation-{action}", service.report(inputs)
    raise ValueError(f"unsupported distillation command: {action}")


def _manifest(value: object) -> ManifestSource:
    if not isinstance(value, Mapping):
        raise ValueError("manifest entries must be objects")
    return ManifestSource(
        ref=_required(value, "ref"),
        path=_required(value, "path"),
        source_paths=_strings(value.get("source_paths", ())),
        operation_refs=_strings(value.get("operation_refs", ())),
        capability_refs=_strings(value.get("capability_refs", ())),
        documentation_refs=_strings(value.get("documentation_refs", ())),
        verification_evidence_refs=_strings(value.get("verification_evidence_refs", ())),
    )


def _required(value: Mapping[object, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"manifest entry requires {key}")
    return item


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise ValueError("distillation declaration lists must contain strings")
    return tuple(value)


def _mapping(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise ValueError("distillation mappings must contain string keys and values")
    return dict(value)


__all__ = ["dispatch_distillation", "load_inputs"]
