from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import InvalidOperationDefinition
from .model import HttpBinding, OperationDefinition

_ID = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InvalidOperationDefinition(f"{where} must be an object")
    return value


def _keys(value: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise InvalidOperationDefinition(f"unsupported field(s) in {where}: {sorted(unknown)}")


def _text(value: Any, where: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidOperationDefinition(f"{where} must be a non-empty string")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise InvalidOperationDefinition(f"{where} has an invalid format")
    return value


def _ref(value: Any, where: str) -> str:
    return _text(value, where, _ID)


def load_operation_definition_from_dict(data: dict[str, Any]) -> OperationDefinition:
    root = _object(data, "manifest")
    _keys(root, {"apiVersion", "kind", "metadata", "spec"}, "manifest")
    if root.get("apiVersion") != "servicefabric.local/v1":
        raise InvalidOperationDefinition("apiVersion must be servicefabric.local/v1")
    if root.get("kind") != "OperationDefinition":
        raise InvalidOperationDefinition("kind must be OperationDefinition")

    metadata = _object(root.get("metadata"), "metadata")
    _keys(metadata, {"id", "version", "name", "description"}, "metadata")
    operation_id = _text(metadata.get("id"), "metadata.id", _ID)
    version = _text(metadata.get("version"), "metadata.version", _VERSION)
    name = metadata.get("name")
    description = metadata.get("description")
    for value, field in ((name, "metadata.name"), (description, "metadata.description")):
        if value is not None and (not isinstance(value, str) or not value):
            raise InvalidOperationDefinition(f"{field} must be a non-empty string")

    spec = _object(root.get("spec"), "spec")
    _keys(spec, {"application_ref", "module_ref", "interface_ref", "bindings"}, "spec")
    bindings_data = spec.get("bindings")
    if not isinstance(bindings_data, list) or not bindings_data:
        raise InvalidOperationDefinition("spec.bindings must be a non-empty list")
    bindings: list[HttpBinding] = []
    seen: set[str] = set()
    allowed = {"id", "protocol", "method", "path", "request_schema_ref", "response_schema_ref", "request_content_type", "response_content_type", "timeout_seconds"}
    for index, raw in enumerate(bindings_data):
        binding = _object(raw, f"spec.bindings[{index}]")
        _keys(binding, allowed, f"spec.bindings[{index}]")
        binding_id = _text(binding.get("id"), f"bindings[{index}].id", _ID)
        if binding_id in seen:
            raise InvalidOperationDefinition(f"duplicate binding id: {binding_id}")
        seen.add(binding_id)
        if binding.get("protocol") != "http":
            raise InvalidOperationDefinition("operation bindings are limited to protocol http")
        method = _text(binding.get("method"), f"bindings[{index}].method")
        if method not in _METHODS:
            raise InvalidOperationDefinition("HTTP method is not supported")
        path = _text(binding.get("path"), f"bindings[{index}].path")
        if not path.startswith("/") or "?" in path or "#" in path or "//" in path or ".." in path:
            raise InvalidOperationDefinition("HTTP binding path must be an absolute, relative-safe path")
        timeout = binding.get("timeout_seconds")
        if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 300):
            raise InvalidOperationDefinition("timeout_seconds must be an integer from 1 through 300")
        values = {}
        for field in ("request_schema_ref", "response_schema_ref"):
            if field in binding:
                values[field] = _ref(binding[field], f"bindings[{index}].{field}")
        for field in ("request_content_type", "response_content_type"):
            values[field] = _text(binding.get(field, "application/json"), f"bindings[{index}].{field}")
        bindings.append(HttpBinding(binding_id, method, path, timeout_seconds=timeout, **values))

    return OperationDefinition(operation_id, version, _ref(spec.get("application_ref"), "spec.application_ref"), _ref(spec.get("module_ref"), "spec.module_ref"), _ref(spec.get("interface_ref"), "spec.interface_ref"), tuple(sorted(bindings, key=lambda item: item.binding_id)), name, description)


def load_operation_definition(path: str | Path) -> OperationDefinition:
    candidate = Path(path)
    try:
        return load_operation_definition_from_dict(json.loads(candidate.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidOperationDefinition(f"cannot read operation definition: {candidate}") from exc
