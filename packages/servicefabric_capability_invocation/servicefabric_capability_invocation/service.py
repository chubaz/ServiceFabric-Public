"""Deterministic canonical capability invocation orchestration."""

from __future__ import annotations

from typing import Any

from servicefabric_capability_registry import CapabilityRegistry
from servicefabric_operation_model import HttpBinding, OperationDefinition

from .errors import BindingResolutionError, CapabilityUnavailableError, OperationResolutionError, SchemaResolutionError
from .models import AvailabilityResolver, CapabilityInvocationRequest, CapabilityInvocationResult, OperationResolver, SchemaResolver, TransportAdapter, TransportInvocation
from .schema import validate_json_schema


class CapabilityInvocationService:
    """Resolve and validate an invocation before delegating to a transport adapter."""

    def __init__(self, registry: CapabilityRegistry, operations: OperationResolver, availability: AvailabilityResolver, schemas: SchemaResolver, transport: TransportAdapter) -> None:
        self._registry = registry
        self._operations = operations
        self._availability = availability
        self._schemas = schemas
        self._transport = transport

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityInvocationResult:
        """Invoke exactly one available capability through the supplied adapter."""
        record = self._registry.describe_capability(request.capability_id)
        operation_id = record.definition.spec.operation_ref
        operation = self._resolve_operation(operation_id)
        if operation.application_ref not in record.application_ids:
            raise OperationResolutionError(f"operation '{operation_id}' is not linked to capability application")
        availability = self._availability.resolve_availability(request.capability_id)
        if not availability.available or not availability.endpoint:
            detail = f": {availability.reason}" if availability.reason else ""
            raise CapabilityUnavailableError(f"capability '{request.capability_id}' is unavailable{detail}")
        binding = self._resolve_binding(operation, request.binding_id)
        if binding.request_schema_ref:
            validate_json_schema(request.input, self._resolve_schema(binding.request_schema_ref))
        output = self._transport.invoke(TransportInvocation(request.capability_id, operation, binding, availability.endpoint, request.input))
        if binding.response_schema_ref:
            validate_json_schema(output, self._resolve_schema(binding.response_schema_ref))
        return CapabilityInvocationResult(request.capability_id, operation.operation_id, binding.binding_id, output)

    def _resolve_operation(self, operation_id: str) -> OperationDefinition:
        try:
            operation = self._operations.resolve_operation(operation_id)
        except Exception as exc:
            raise OperationResolutionError(f"operation '{operation_id}' could not be resolved") from exc
        if not isinstance(operation, OperationDefinition) or operation.operation_id != operation_id:
            raise OperationResolutionError(f"operation resolver returned an invalid definition for '{operation_id}'")
        return operation

    @staticmethod
    def _resolve_binding(operation: OperationDefinition, binding_id: str | None) -> HttpBinding:
        bindings = tuple(sorted(operation.bindings, key=lambda binding: binding.binding_id))
        if binding_id is None:
            if not bindings:
                raise BindingResolutionError(f"operation '{operation.operation_id}' has no reviewed HTTP bindings")
            return bindings[0]
        for binding in bindings:
            if binding.binding_id == binding_id:
                return binding
        raise BindingResolutionError(f"binding '{binding_id}' is not defined by operation '{operation.operation_id}'")

    def _resolve_schema(self, schema_ref: str) -> Any:
        try:
            schema = self._schemas.resolve_schema(schema_ref)
        except Exception as exc:
            raise SchemaResolutionError(f"schema '{schema_ref}' could not be resolved") from exc
        if not isinstance(schema, dict):
            raise SchemaResolutionError(f"schema resolver returned an invalid schema for '{schema_ref}'")
        return schema
