"""Reviewed operation, capability, schema, and effect declarations for Research Notes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _note_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
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


def research_notes_declarations() -> dict[str, dict[str, Any]]:
    """Return caller-owned explicit static declarations for the three note actions."""
    note = _note_schema()
    declarations = {
        ".servicefabric/operations/create-note.yaml": {
            "apiVersion": "servicefabric.local/v1",
            "kind": "OperationDefinition",
            "metadata": {"id": "create-note", "name": "Create note"},
            "spec": {
                "applicationId": "research-notes",
                "moduleId": "notes-api",
                "interfaceRef": "notes-api",
                "inputSchemaRef": "schemas/create-note.input.schema.json",
                "outputSchemaRef": "schemas/note.output.schema.json",
                "effects": [{"id": "notes.write", "kind": "data.write", "targetRef": "notes-db"}],
            },
        },
        ".servicefabric/operations/get-note.yaml": {
            "apiVersion": "servicefabric.local/v1",
            "kind": "OperationDefinition",
            "metadata": {"id": "get-note", "name": "Get note"},
            "spec": {
                "applicationId": "research-notes",
                "moduleId": "notes-api",
                "interfaceRef": "notes-api",
                "inputSchemaRef": "schemas/get-note.input.schema.json",
                "outputSchemaRef": "schemas/note.output.schema.json",
                "effects": [{"id": "notes.read", "kind": "data.read", "targetRef": "notes-db"}],
            },
        },
        ".servicefabric/operations/search-notes.yaml": {
            "apiVersion": "servicefabric.local/v1",
            "kind": "OperationDefinition",
            "metadata": {"id": "search-notes", "name": "Search notes"},
            "spec": {
                "applicationId": "research-notes",
                "moduleId": "notes-api",
                "interfaceRef": "notes-api",
                "inputSchemaRef": "schemas/search-notes.input.schema.json",
                "outputSchemaRef": "schemas/search-notes.output.schema.json",
                "effects": [{"id": "notes.read", "kind": "data.read", "targetRef": "notes-db"}],
            },
        },
        ".servicefabric/capabilities/notes.create.yaml": {
            "apiVersion": "servicefabric.local/v1",
            "kind": "CapabilityDefinition",
            "metadata": {"id": "notes.create", "name": "Create note"},
            "spec": {"applicationId": "research-notes", "operationRef": "create-note", "effects": [{"id": "notes.write", "kind": "data.write", "targetRef": "notes-db"}]},
        },
        ".servicefabric/capabilities/notes.get.yaml": {
            "apiVersion": "servicefabric.local/v1",
            "kind": "CapabilityDefinition",
            "metadata": {"id": "notes.get", "name": "Get note"},
            "spec": {"applicationId": "research-notes", "operationRef": "get-note", "effects": [{"id": "notes.read", "kind": "data.read", "targetRef": "notes-db"}]},
        },
        ".servicefabric/capabilities/notes.search.yaml": {
            "apiVersion": "servicefabric.local/v1",
            "kind": "CapabilityDefinition",
            "metadata": {"id": "notes.search", "name": "Search notes"},
            "spec": {"applicationId": "research-notes", "operationRef": "search-notes", "effects": [{"id": "notes.read", "kind": "data.read", "targetRef": "notes-db"}]},
        },
        ".servicefabric/schemas/create-note.input.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "required": ["title", "body"], "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 200}, "body": {"type": "string", "minLength": 1, "maxLength": 100000}}},
        ".servicefabric/schemas/get-note.input.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "required": ["note_id"], "properties": {"note_id": {"type": "integer", "minimum": 1}}},
        ".servicefabric/schemas/search-notes.input.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "properties": {"query": {"type": "string", "maxLength": 200, "default": ""}}},
        ".servicefabric/schemas/note.output.schema.json": note,
        ".servicefabric/schemas/search-notes.output.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "required": ["notes"], "properties": {"notes": {"type": "array", "items": note}}},
    }
    return deepcopy(declarations)
