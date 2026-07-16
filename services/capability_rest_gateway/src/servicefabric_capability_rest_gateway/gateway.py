"""Transport-neutral JSON projection of the integration capability facade."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Protocol


class CapabilityConsumerBoundary(Protocol):
    """Small consumer-facing boundary supplied by integration composition."""

    def list_capabilities(self, application_id: str | None = None) -> tuple[object, ...]: ...

    def describe_capability(self, capability_id: str) -> object: ...

    def capability_availability(self, capability_id: str) -> object: ...

    def invoke_capability(self, capability_id: str, input_value: object) -> object: ...


class CapabilityRestGateway:
    """Map integration-owned facade results into deterministic JSON values."""

    def __init__(self, consumer: CapabilityConsumerBoundary) -> None:
        self._consumer = consumer

    def list_capabilities(self, application_id: str | None = None) -> dict[str, object]:
        descriptions = self._consumer.list_capabilities(application_id)
        return {"capabilities": [_description_json(value) for value in descriptions]}

    def describe_capability(self, capability_id: str) -> dict[str, object]:
        return _description_json(self._consumer.describe_capability(capability_id))

    def availability(self, capability_id: str) -> dict[str, str]:
        return _availability_json(self._consumer.capability_availability(capability_id))

    def invoke(self, capability_id: str, input_value: object) -> dict[str, object]:
        return _invocation_json(self._consumer.invoke_capability(capability_id, input_value))


def _description_json(value: object) -> dict[str, object]:
    return {
        "applicationIds": list(_strings(value, "application_ids")),
        "capabilityId": _string(value, "capability_id"),
        "digest": _string(value, "digest"),
        "objective": _string(value, "objective"),
        "operationId": _string(value, "operation_id"),
        "title": _string(value, "title"),
    }


def _availability_json(value: object) -> dict[str, str]:
    return {
        "applicationId": _string(value, "application_id"),
        "capabilityId": _string(value, "capability_id"),
        "moduleId": _string(value, "module_id"),
        "reason": _string(value, "reason"),
        "state": _string(value, "state"),
    }


def _invocation_json(value: object) -> dict[str, object]:
    return {
        "bindingId": _string(value, "binding_id"),
        "capabilityId": _string(value, "capability_id"),
        "operationId": _string(value, "operation_id"),
        "output": _json_value(getattr(value, "output")),
    }


def _string(value: object, name: str) -> str:
    result = getattr(value, name)
    if not isinstance(result, str):
        raise TypeError(f"facade {name} must be a string")
    return result


def _strings(value: object, name: str) -> tuple[str, ...]:
    result = getattr(value, name)
    if not isinstance(result, tuple) or not all(isinstance(item, str) for item in result):
        raise TypeError(f"facade {name} must be a tuple of strings")
    return result


def _json_value(value: object) -> object:
    """Convert immutable facade output to an RFC 8259 JSON value."""

    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Enum):
        return _json_value(value.value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"facade returned a non-JSON-compatible {type(value).__name__}")
