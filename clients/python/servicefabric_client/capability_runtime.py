"""Integration composition for registered capability availability and invocation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from servicefabric_capability_invocation import (
    CapabilityAvailability as InvocationAvailability,
    CapabilityInvocationRequest,
    CapabilityInvocationService,
    TransportInvocation,
)
from servicefabric_capability_registry import CapabilityRecord
from servicefabric_capability_runtime import (
    CapabilityAvailability,
    CapabilityAvailabilityResolver,
    CapabilityRuntimeTarget,
    ModuleHealth,
)
from servicefabric_http_operation_adapter import HttpOperationAdapter
from servicefabric_operation_model import OperationDefinition
from servicefabric_process_runtime import ManagedProcessController
from servicefabric_workspace import ApplicationLayout, WorkspaceLayout

from .capabilities import CapabilityValidationError, registry_for_workspace, validate_generated_capabilities


class CapabilityRuntimeCompositionError(ValueError):
    """Raised when reviewed application declarations cannot compose a call."""


class CapabilityRuntimeService:
    """Compose static definitions with live local module observations."""

    def __init__(
        self,
        workspace: WorkspaceLayout,
        *,
        processes: ManagedProcessController | None = None,
        http_adapter: HttpOperationAdapter | None = None,
    ) -> None:
        self._workspace = workspace
        self._registry = registry_for_workspace(workspace)
        self._processes = processes or ManagedProcessController(workspace)
        self._http_adapter = http_adapter or HttpOperationAdapter()

    def availability(self, capability_id: str) -> CapabilityAvailability:
        """Return runtime-only availability for one static capability."""

        record = self._registry.describe(capability_id)
        _, operation = self._resolve_owner(record)
        target = CapabilityRuntimeTarget(
            capability_id=capability_id,
            application_id=operation.application_ref,
            module_id=operation.module_ref,
        )
        return CapabilityAvailabilityResolver(_ProcessModuleHealthSource(self._processes)).resolve(target)

    def availability_for_application(self, application_id: str) -> tuple[CapabilityAvailability, ...]:
        """Return deterministic availability records for one registered application."""

        return tuple(self.availability(record.definition.metadata.id) for record in self._registry.list(application_id))

    def invoke(self, capability_id: str, input_value: Any) -> dict[str, Any]:
        """Invoke one available capability through the reviewed HTTP adapter."""

        record = self._registry.describe(capability_id)
        application_id, operation = self._resolve_owner(record)
        service = CapabilityInvocationService(
            self._registry,
            _OperationResolver(operation),
            _InvocationAvailabilityResolver(self, application_id, operation.module_ref),
            _SchemaResolver(self._application_layout(application_id)),
            _HttpTransportAdapter(self._http_adapter),
        )
        result = service.invoke(CapabilityInvocationRequest(capability_id, input_value))
        return {
            "capability_id": result.capability_id,
            "operation_id": result.operation_id,
            "binding_id": result.binding_id,
            "output": result.output,
        }

    def _resolve_owner(self, record: CapabilityRecord) -> tuple[str, OperationDefinition]:
        matches: list[tuple[str, OperationDefinition]] = []
        for application_id in record.application_ids:
            try:
                definitions = validate_generated_capabilities(self._workspace, application_id)
            except CapabilityValidationError as exc:
                raise CapabilityRuntimeCompositionError(str(exc)) from exc
            for operation in definitions.operations:
                if operation.operation_id == record.definition.spec.operation_ref and operation.application_ref == application_id:
                    matches.append((application_id, operation))
        if len(matches) != 1:
            raise CapabilityRuntimeCompositionError(
                f"capability '{record.definition.metadata.id}' must resolve to exactly one owning application and operation"
            )
        return matches[0]

    def _application_layout(self, application_id: str) -> ApplicationLayout:
        return ApplicationLayout.from_application_id(application_id, self._workspace.applications)


class _ProcessModuleHealthSource:
    def __init__(self, processes: ManagedProcessController) -> None:
        self._processes = processes

    def get_module_health(self, application_id: str, module_id: str) -> ModuleHealth:
        status = self._processes.status(application_id, module_id)
        return ModuleHealth(application_id, module_id, status.state, status.health)


class _OperationResolver:
    def __init__(self, operation: OperationDefinition) -> None:
        self._operation = operation

    def resolve_operation(self, operation_id: str) -> OperationDefinition:
        if operation_id != self._operation.operation_id:
            raise LookupError(operation_id)
        return self._operation


class _InvocationAvailabilityResolver:
    def __init__(self, service: CapabilityRuntimeService, application_id: str, module_id: str) -> None:
        self._service = service
        self._application_id = application_id
        self._module_id = module_id

    def resolve_availability(self, capability_id: str) -> InvocationAvailability:
        availability = self._service.availability(capability_id)
        status = self._service._processes.status(self._application_id, self._module_id)
        endpoint = f"http://127.0.0.1:{status.port}" if availability.available and status.port is not None else None
        return InvocationAvailability(availability.available, endpoint, availability.reason.value)


class _SchemaResolver:
    def __init__(self, application: ApplicationLayout) -> None:
        self._schemas = self._load(application.root / ".servicefabric" / "schemas")

    def resolve_schema(self, schema_ref: str) -> Mapping[str, Any]:
        try:
            return self._schemas[schema_ref]
        except KeyError as exc:
            raise LookupError(schema_ref) from exc

    @staticmethod
    def _load(directory: Path) -> dict[str, Mapping[str, Any]]:
        schemas: dict[str, Mapping[str, Any]] = {}
        if not directory.is_dir() or directory.is_symlink():
            raise CapabilityRuntimeCompositionError("generated schema directory is missing or unsafe")
        for path in sorted(directory.glob("*.schema.json")):
            if path.is_symlink():
                raise CapabilityRuntimeCompositionError("generated schema declaration is unsafe")
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CapabilityRuntimeCompositionError("generated schema declaration is invalid") from exc
            schema_id = value.get("$id") if isinstance(value, dict) else None
            if not isinstance(schema_id, str) or not schema_id or schema_id in schemas:
                raise CapabilityRuntimeCompositionError("generated schema identifiers must be unique")
            schemas[schema_id] = value
        return schemas


class _HttpTransportAdapter:
    def __init__(self, adapter: HttpOperationAdapter) -> None:
        self._adapter = adapter

    def invoke(self, request: TransportInvocation) -> Any:
        return self._adapter.invoke(request.endpoint, request.binding, request.input)
