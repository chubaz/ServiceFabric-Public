"""Reviewed operation, capability, schema, and effect declarations for Research Notes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_SCHEMA = "https://json-schema.org/draft/2020-12/schema"


def _effect(effect_type: str) -> dict[str, Any]:
    return {
        "effects": [{
            "effect_type": effect_type,
            "target_category": "database",
            "scope": "Research Notes records",
            "reversibility": "compensatable" if effect_type == "database_write" else "not_applicable",
            "verification_required": effect_type == "database_write",
            "approval_required": False,
            "idempotency_required": effect_type == "database_write",
        }],
    }


def _note_schema() -> dict[str, Any]:
    return {
        "$schema": _SCHEMA,
        "$id": "notes.note-output",
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "title", "body", "created_at"],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "body": {"type": "string", "minLength": 1, "maxLength": 100000},
            "created_at": {"type": "string", "format": "date-time"},
        },
    }


def _operation(operation_id: str, *, method: str, path: str, request_schema: str | None, response_schema: str) -> dict[str, Any]:
    binding: dict[str, Any] = {
        "id": f"{operation_id}-http",
        "protocol": "http",
        "method": method,
        "path": path,
        "response_schema_ref": response_schema,
        "timeout_seconds": 10,
    }
    if request_schema is not None:
        binding["request_schema_ref"] = request_schema
    return {
        "apiVersion": "servicefabric.local/v1",
        "kind": "OperationDefinition",
        "metadata": {"id": operation_id, "version": "1.0.0", "name": operation_id.replace("-", " ").capitalize()},
        "spec": {
            "application_ref": "research-notes",
            "module_ref": "notes-api",
            "interface_ref": "notes-api",
            "bindings": [binding],
        },
    }


def _capability(capability_id: str, operation_id: str, *, effect_type: str, objective: str, capability_class: str, inputs: list[str], outputs: list[str]) -> dict[str, Any]:
    return {
        "apiVersion": "servicefabric.local/v1",
        "kind": "CapabilityDefinition",
        "metadata": {"id": capability_id, "title": operation_id.replace("-", " ").capitalize(), "domain": "notes"},
        "spec": {
            "operationRef": operation_id,
            "objective": objective,
            "capabilityClass": capability_class,
            "concepts": ["research notes", "note records"],
            "expectedInputs": inputs,
            "expectedOutputs": outputs,
            "effects": _effect(effect_type),
            "suitableFor": [objective],
            "unsuitableFor": ["Capability invocation, registry registration, or consumer projection."],
            "qualityDimensions": ["bounded inputs", "deterministic contract"],
        },
    }


def research_notes_declarations() -> dict[str, dict[str, Any]]:
    """Return caller-owned static declarations for the three explicitly reviewed actions."""
    note = _note_schema()
    declarations = {
        ".servicefabric/operations/create-note.yaml": _operation("create-note", method="POST", path="/notes", request_schema="notes.create-note-input", response_schema="notes.note-output"),
        ".servicefabric/operations/get-note.yaml": _operation("get-note", method="GET", path="/notes/{note_id}", request_schema="notes.get-note-input", response_schema="notes.note-output"),
        ".servicefabric/operations/search-notes.yaml": _operation("search-notes", method="GET", path="/notes", request_schema="notes.search-notes-input", response_schema="notes.search-notes-output"),
        ".servicefabric/capabilities/notes.create.yaml": _capability("notes.create", "create-note", effect_type="database_write", objective="Create one validated Research Notes record.", capability_class="creation", inputs=["note title", "note body"], outputs=["created note record"]),
        ".servicefabric/capabilities/notes.get.yaml": _capability("notes.get", "get-note", effect_type="database_read", objective="Retrieve one Research Notes record by identifier.", capability_class="retrieval", inputs=["note identifier"], outputs=["note record"]),
        ".servicefabric/capabilities/notes.search.yaml": _capability("notes.search", "search-notes", effect_type="database_read", objective="Search Research Notes records using an optional query.", capability_class="retrieval", inputs=["optional note query"], outputs=["matching note records"]),
        ".servicefabric/schemas/create-note.input.schema.json": {"$schema": _SCHEMA, "$id": "notes.create-note-input", "type": "object", "additionalProperties": False, "required": ["title", "body"], "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 200}, "body": {"type": "string", "minLength": 1, "maxLength": 100000}}},
        ".servicefabric/schemas/get-note.input.schema.json": {"$schema": _SCHEMA, "$id": "notes.get-note-input", "type": "object", "additionalProperties": False, "required": ["note_id"], "properties": {"note_id": {"type": "integer", "minimum": 1}}},
        ".servicefabric/schemas/search-notes.input.schema.json": {"$schema": _SCHEMA, "$id": "notes.search-notes-input", "type": "object", "additionalProperties": False, "properties": {"query": {"type": "string", "maxLength": 200, "default": ""}}},
        ".servicefabric/schemas/note.output.schema.json": note,
        ".servicefabric/schemas/search-notes.output.schema.json": {"$schema": _SCHEMA, "$id": "notes.search-notes-output", "type": "object", "additionalProperties": False, "required": ["notes"], "properties": {"notes": {"type": "array", "items": note}}},
    }
    return deepcopy(declarations)
