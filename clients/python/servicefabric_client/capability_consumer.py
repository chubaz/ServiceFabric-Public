"""Projection-neutral consumer facade for registered capabilities."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias

from servicefabric_capability_registry import CapabilityRecord, CapabilityRegistry
from servicefabric_workspace import WorkspaceLayout

from .capabilities import registry_for_workspace
from .capability_runtime import CapabilityRuntimeService


FrozenValue: TypeAlias = object


@dataclass(frozen=True, slots=True)
class FrozenMapping(Mapping[str, FrozenValue]):
    """An immutable, key-sorted mapping for consumer-facing output values."""

    entries: tuple[tuple[str, FrozenValue], ...]

    def __getitem__(self, key: str) -> FrozenValue:
        for item_key, value in self.entries:
            if item_key == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self.entries)

    def __len__(self) -> int:
        return len(self.entries)


@dataclass(frozen=True, slots=True)
class CapabilityDescription:
    """Stable static declaration data available after an application stops."""

    capability_id: str
    title: str
    objective: str
    operation_id: str
    digest: str
    application_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapabilityAvailability:
    """Immutable availability view supplied by the runtime."""

    capability_id: str
    application_id: str
    module_id: str
    state: str
    reason: str

    @property
    def available(self) -> bool:
        return self.state == "available"


@dataclass(frozen=True, slots=True)
class CapabilityInvocation:
    """Immutable result of the canonical runtime invocation."""

    capability_id: str
    operation_id: str
    binding_id: str
    output: FrozenValue


class _CapabilityRuntime(Protocol):
    def availability(self, capability_id: str) -> object: ...

    def availability_for_application(self, application_id: str) -> tuple[object, ...]: ...

    def invoke(self, capability_id: str, input_value: object) -> Mapping[str, object]: ...


class CapabilityConsumerFacade:
    """Expose static discovery and runtime calls without projection behavior."""

    def __init__(self, registry: CapabilityRegistry, runtime: _CapabilityRuntime) -> None:
        self._registry = registry
        self._runtime = runtime

    @classmethod
    def for_workspace(
        cls,
        workspace: WorkspaceLayout,
        *,
        runtime: CapabilityRuntimeService | None = None,
    ) -> "CapabilityConsumerFacade":
        """Compose the Wave-4 registry and Wave-5 runtime in one integration owner."""

        return cls(registry_for_workspace(workspace), runtime or CapabilityRuntimeService(workspace))

    def list_capabilities(self, application_id: str | None = None) -> tuple[CapabilityDescription, ...]:
        """List persisted static declarations in registry order."""

        return tuple(_description(record) for record in self._registry.list(application_id))

    def describe_capability(self, capability_id: str) -> CapabilityDescription:
        """Describe one persisted static declaration."""

        return _description(self._registry.describe(capability_id))

    def capability_availability(self, capability_id: str) -> CapabilityAvailability:
        """Delegate one availability lookup to the Wave-5 runtime."""

        return _availability(self._runtime.availability(capability_id))

    def availability_for_application(self, application_id: str) -> tuple[CapabilityAvailability, ...]:
        """Delegate application-scoped availability to the Wave-5 runtime."""

        return tuple(_availability(value) for value in self._runtime.availability_for_application(application_id))

    def invoke_capability(self, capability_id: str, input_value: object) -> CapabilityInvocation:
        """Delegate canonical invocation without schema or transport handling."""

        result = self._runtime.invoke(capability_id, input_value)
        return CapabilityInvocation(
            capability_id=_required_string(result, "capability_id"),
            operation_id=_required_string(result, "operation_id"),
            binding_id=_required_string(result, "binding_id"),
            output=_freeze(result.get("output")),
        )


def _description(record: CapabilityRecord) -> CapabilityDescription:
    definition = record.definition
    return CapabilityDescription(
        capability_id=definition.metadata.id,
        title=definition.metadata.title,
        objective=definition.spec.objective,
        operation_id=definition.spec.operation_ref,
        digest=record.digest,
        application_ids=tuple(sorted(record.application_ids)),
    )


def _availability(value: object) -> CapabilityAvailability:
    return CapabilityAvailability(
        capability_id=_attribute_string(value, "capability_id"),
        application_id=_attribute_string(value, "application_id"),
        module_id=_attribute_string(value, "module_id"),
        state=_enum_value(value, "state"),
        reason=_enum_value(value, "reason"),
    )


def _attribute_string(value: object, name: str) -> str:
    result = getattr(value, name)
    if not isinstance(result, str):
        raise TypeError(f"runtime {name} must be a string")
    return result


def _enum_value(value: object, name: str) -> str:
    result = getattr(value, name)
    scalar = getattr(result, "value", result)
    if not isinstance(scalar, str):
        raise TypeError(f"runtime {name} must be a string value")
    return scalar


def _required_string(value: Mapping[str, object], name: str) -> str:
    result = value.get(name)
    if not isinstance(result, str):
        raise TypeError(f"runtime invocation {name} must be a string")
    return result


def _freeze(value: object) -> FrozenValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        pairs = ((str(key), _freeze(item)) for key, item in value.items())
        return FrozenMapping(tuple(sorted(pairs, key=lambda item: item[0])))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    raise TypeError(f"runtime invocation output must be JSON-compatible, got {type(value).__name__}")
