"""Transport-neutral REST facade that delegates to one capability runtime."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Protocol


class CapabilityRuntimeBoundary(Protocol):
    """Public operations required from the composed capability runtime."""

    def list_capabilities(self, application_id: str | None = None) -> Iterable[object]: ...

    def describe_capability(self, capability_id: str) -> object: ...

    def availability(self, capability_id: str) -> object: ...

    def invoke(self, capability_id: str, input_value: Any) -> object: ...


class CapabilityRestGateway:
    """Project runtime responses as JSON values without owning runtime logic."""

    def __init__(self, runtime: CapabilityRuntimeBoundary) -> None:
        self._runtime = runtime

    def list_capabilities(self, application_id: str | None = None) -> dict[str, object]:
        records = self._runtime.list_capabilities(application_id)
        return {"capabilities": [_json_value(record) for record in records]}

    def describe_capability(self, capability_id: str) -> object:
        return _json_value(self._runtime.describe_capability(capability_id))

    def availability(self, capability_id: str) -> object:
        return _json_value(self._runtime.availability(capability_id))

    def invoke(self, capability_id: str, input_value: Any) -> object:
        return _json_value(self._runtime.invoke(capability_id, input_value))


def _json_value(value: object) -> object:
    """Convert supported runtime records into JSON-compatible values."""

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json", by_alias=True)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _json_value(to_dict())
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Enum):
        return _json_value(value.value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"runtime returned a non-JSON-compatible {type(value).__name__}")
