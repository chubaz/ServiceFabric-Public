"""Atomic, deterministic materialization of reviewed application blueprints."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from servicefabric_application_model import load_module_definition_from_dict, validate_module_graph
from servicefabric_blueprints import ApplicationBlueprint

from .errors import GenerationCollision, GenerationRollback, InvalidGenerationParameter

_TOKEN = re.compile(r"(?:\$\{([a-z][a-z0-9_-]*)\}|\{\{\s*([a-z][a-z0-9_-]*)\s*\}\})")
_PARAMETER = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


@dataclass(frozen=True)
class GenerationRequest:
    """Inputs for one application generation transaction."""

    application_id: str
    display_name: str
    blueprint: ApplicationBlueprint
    destination: Path
    parameters: Mapping[str, str] = ()


@dataclass(frozen=True)
class GenerationResult:
    """Published generated application and its deterministic file inventory."""

    application_id: str
    root: Path
    module_ids: tuple[str, ...]
    files: tuple[Path, ...]


class ApplicationGenerator:
    """Materializes reviewed blueprints without mutating an existing target."""

    def generate(self, request: GenerationRequest) -> GenerationResult:
        _validate_request(request)
        target = request.destination / request.application_id
        if target.exists():
            raise GenerationCollision(f"Application target already exists: '{target}'.")

        parent = request.destination
        parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{request.application_id}.", dir=parent))
        try:
            manifests = _materialized_manifests(request)
            modules = tuple(load_module_definition_from_dict(item) for item in manifests)
            validate_module_graph(list(modules))
            _write_application(staging, request, manifests)
            staging.rename(target)
        except Exception as exc:
            shutil.rmtree(staging, ignore_errors=True)
            if isinstance(exc, (GenerationCollision, InvalidGenerationParameter)):
                raise
            raise GenerationRollback(f"Generation of '{request.application_id}' rolled back: {exc}") from exc

        files = tuple(sorted(path.relative_to(target) for path in target.rglob("*") if path.is_file()))
        return GenerationResult(request.application_id, target, tuple(item["metadata"]["id"] for item in manifests), files)

    create = generate


def materialize_blueprint(
    blueprint: ApplicationBlueprint,
    destination: Path,
    application_id: str,
    display_name: str,
    parameters: Mapping[str, str] | None = None,
) -> GenerationResult:
    """Convenience API for atomic blueprint materialization."""
    return ApplicationGenerator().generate(GenerationRequest(
        application_id, display_name, blueprint, Path(destination), parameters or {}
    ))


def validate_parameters(
    blueprint: ApplicationBlueprint, parameters: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Validate and normalize the complete parameter set required by a blueprint."""
    supplied = dict(parameters or {})
    names: set[str] = set()
    for manifest in blueprint.module_manifests():
        for value in _walk_strings(manifest):
            names.update(a or b for a, b in _TOKEN.findall(value))
    unknown = sorted(set(supplied) - names)
    if unknown:
        raise InvalidGenerationParameter(f"Unknown generation parameter(s): {', '.join(unknown)}.")
    for name, value in supplied.items():
        if not _PARAMETER.fullmatch(name) or not isinstance(value, str) or not value.strip():
            raise InvalidGenerationParameter(f"Invalid generation parameter '{name}'.")
        if "\x00" in value or ".." in Path(value).parts:
            raise InvalidGenerationParameter(f"Unsafe generation parameter '{name}'.")
    missing = sorted(names - set(supplied))
    if missing:
        raise InvalidGenerationParameter(f"Missing generation parameter(s): {', '.join(missing)}.")
    return supplied


def _validate_request(request: GenerationRequest) -> None:
    if not _PARAMETER.fullmatch(request.application_id):
        raise InvalidGenerationParameter("application_id must be a lowercase identifier.")
    if not request.display_name.strip():
        raise InvalidGenerationParameter("display_name cannot be empty.")
    if not request.destination.is_absolute():
        raise InvalidGenerationParameter("destination must be an absolute path.")
    validate_parameters(request.blueprint, request.parameters)


def _replace(value: Any, parameters: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        names = {a or b for a, b in _TOKEN.findall(value)}
        missing = sorted(names - set(parameters))
        if missing:
            raise InvalidGenerationParameter(f"Missing generation parameter(s): {', '.join(missing)}.")
        return _TOKEN.sub(lambda match: str(parameters[match.group(1) or match.group(2)]), value)
    if isinstance(value, list):
        return [_replace(item, parameters) for item in value]
    if isinstance(value, dict):
        return {key: _replace(item, parameters) for key, item in value.items()}
    return value


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def _materialized_manifests(request: GenerationRequest) -> tuple[dict[str, Any], ...]:
    result = []
    for module in request.blueprint.modules:
        manifest = _replace(module.to_manifest(), request.parameters)
        manifest["spec"]["source"] = f"modules/{manifest['metadata']['id']}"
        result.append(manifest)
    return tuple(result)


def _write_application(root: Path, request: GenerationRequest, manifests: tuple[dict[str, Any], ...]) -> None:
    (root / "modules").mkdir()
    (root / "tests").mkdir()
    (root / "docs").mkdir()
    (root / ".servicefabric" / "generated").mkdir(parents=True)
    _write(root / "README.md", f"# {request.display_name}\n\nGenerated ServiceFabric application `{request.application_id}`.\n")
    _write(root / "AGENTS.md", "# Application Development Instructions\n\nEdit `modules/` and `tests/`; generated files are managed by ServiceFabric.\n")
    _write(root / "ARCHITECTURE.md", f"# Architecture of {request.display_name}\n\nGenerated from blueprint `{request.blueprint.blueprint_id}`.\n")
    _write(root / "DEVELOPMENT.md", "# Development\n\nUse the ServiceFabric application lifecycle commands.\n")
    _write_json_yaml(root / ".servicefabric" / "application.yaml", {"apiVersion":"servicefabric.local/v1", "kind":"Application", "metadata":{"id":request.application_id,"name":request.display_name}, "spec":{"status":"development","modules":[m["metadata"]["id"] for m in manifests]}})
    _write_json_yaml(root / ".servicefabric" / "blueprint.yaml", {"apiVersion":"servicefabric.local/v1", "kind":"ApplicationBlueprint", "metadata":{"applicationId":request.application_id}, "spec":{"source":request.blueprint.blueprint_id,"version":request.blueprint.version,"modules":[m["metadata"]["id"] for m in manifests]}})
    _write_json_yaml(root / ".servicefabric" / "bindings.yaml", {"apiVersion":"servicefabric.local/v1","kind":"ApplicationBindings","metadata":{"applicationId":request.application_id},"spec":{"bindings":{}}})
    _write_json_yaml(root / ".servicefabric" / "development.yaml", {"apiVersion":"servicefabric.local/v1","kind":"DevelopmentConfiguration","metadata":{"applicationId":request.application_id},"spec":{"commands":{},"requiredChecks":[]}})
    for manifest in manifests:
        module_id = manifest["metadata"]["id"]
        module_root = root / "modules" / module_id
        module_root.mkdir()
        _write_json_yaml(module_root / "module.yaml", manifest)
        if manifest["spec"]["primitive"] in {"service", "web"}:
            _write(module_root / "app.py", "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/health')\ndef health() -> dict[str, str]:\n    return {'status': 'ok'}\n")
        else:
            _write(module_root / "main.py", "def main() -> None:\n    pass\n")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_json_yaml(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
