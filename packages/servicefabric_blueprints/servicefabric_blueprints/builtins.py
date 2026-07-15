"""Built-in reviewed application blueprints."""

from __future__ import annotations

from servicefabric_blueprints.catalog import BlueprintCatalog
from servicefabric_blueprints.definitions import ApplicationBlueprint, BlueprintFile, BlueprintModule

FASTAPI_SERVICE_KIT = (
    "fastapi-service @ServiceFabric/portfolio/applications/"
    "revisions/examples.hello-static-1.0.0.json"
)


def _research_notes_files() -> dict[str, dict]:
    note = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "required": ["id", "title", "body", "created_at"], "properties": {"id": {"type": "integer", "minimum": 1}, "title": {"type": "string", "minLength": 1, "maxLength": 200}, "body": {"type": "string", "minLength": 1, "maxLength": 100000}, "created_at": {"type": "string", "format": "date-time"}}}
    def operation(operation_id: str, input_schema: str, output_schema: str, effect_kind: str) -> dict:
        return {"apiVersion": "servicefabric.local/v1", "kind": "OperationDefinition", "metadata": {"id": operation_id, "name": operation_id.replace("-", " ").capitalize()}, "spec": {"applicationId": "research-notes", "moduleId": "notes-api", "interfaceRef": "notes-api", "inputSchemaRef": input_schema, "outputSchemaRef": output_schema, "effects": [{"id": "notes.write" if effect_kind == "data.write" else "notes.read", "kind": effect_kind, "targetRef": "notes-db"}]}}
    def capability(capability_id: str, operation_id: str, effect_kind: str) -> dict:
        return {"apiVersion": "servicefabric.local/v1", "kind": "CapabilityDefinition", "metadata": {"id": capability_id, "name": operation_id.replace("-", " ").capitalize()}, "spec": {"applicationId": "research-notes", "operationRef": operation_id, "effects": [{"id": "notes.write" if effect_kind == "data.write" else "notes.read", "kind": effect_kind, "targetRef": "notes-db"}]}}
    return {
        ".servicefabric/operations/create-note.yaml": operation("create-note", "schemas/create-note.input.schema.json", "schemas/note.output.schema.json", "data.write"),
        ".servicefabric/operations/get-note.yaml": operation("get-note", "schemas/get-note.input.schema.json", "schemas/note.output.schema.json", "data.read"),
        ".servicefabric/operations/search-notes.yaml": operation("search-notes", "schemas/search-notes.input.schema.json", "schemas/search-notes.output.schema.json", "data.read"),
        ".servicefabric/capabilities/notes.create.yaml": capability("notes.create", "create-note", "data.write"),
        ".servicefabric/capabilities/notes.get.yaml": capability("notes.get", "get-note", "data.read"),
        ".servicefabric/capabilities/notes.search.yaml": capability("notes.search", "search-notes", "data.read"),
        ".servicefabric/schemas/create-note.input.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "required": ["title", "body"], "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 200}, "body": {"type": "string", "minLength": 1, "maxLength": 100000}}},
        ".servicefabric/schemas/get-note.input.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "required": ["note_id"], "properties": {"note_id": {"type": "integer", "minimum": 1}}},
        ".servicefabric/schemas/search-notes.input.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "properties": {"query": {"type": "string", "maxLength": 200, "default": ""}}},
        ".servicefabric/schemas/note.output.schema.json": note,
        ".servicefabric/schemas/search-notes.output.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False, "required": ["notes"], "properties": {"notes": {"type": "array", "items": note}}},
    }


TEXT_UTILITY_BLUEPRINT = ApplicationBlueprint(
    blueprint_id="text-utility",
    version="0.1.0",
    title="Text Utility",
    description="Single service module for the reviewed Text Utility fixture.",
    modules=(
        BlueprintModule.from_manifest(
            {
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "text-api", "version": "0.1.0"},
                "spec": {
                    "primitive": "service",
                    "kit": FASTAPI_SERVICE_KIT,
                    "source": "examples/text-utility",
                    "provides": [
                        {"id": "text-api", "type": "http", "protocol": "http"}
                    ],
                    "lifecycle": {
                        "readiness": {"type": "http", "path": "/health"},
                        "shutdown": {"timeoutSeconds": 10},
                    },
                    "resourceExpectations": {"memoryMiB": 256, "cpuCores": 0.25},
                },
            }
        ),
    ),
)


RESEARCH_NOTES_BLUEPRINT = ApplicationBlueprint(
    blueprint_id="research-notes",
    version="0.1.0",
    title="Research Notes",
    description="Single service module with an explicit local database resource request.",
    modules=(
        BlueprintModule.from_manifest(
            {
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "notes-api", "version": "0.1.0"},
                "spec": {
                    "primitive": "service",
                    "kit": FASTAPI_SERVICE_KIT,
                    "source": "examples/research-notes/api",
                    "provides": [
                        {"id": "notes-api", "type": "http", "protocol": "http"}
                    ],
                    "requires": {
                        "resources": [
                            {
                                "id": "notes-db",
                                "type": "postgres",
                                "scope": "application",
                            }
                        ]
                    },
                    "lifecycle": {
                        "startAfter": ["notes-db"],
                        "readiness": {"type": "http", "path": "/health"},
                        "shutdown": {"timeoutSeconds": 10},
                    },
                    "resourceExpectations": {"memoryMiB": 256, "cpuCores": 0.25},
                },
            }
        ),
    ),
    static_files=tuple(
        BlueprintFile(path=path, document=document)
        for path, document in sorted(_research_notes_files().items())
    ),
)


def create_default_blueprint_catalog() -> BlueprintCatalog:
    """Creates a catalog with all built-in reviewed blueprints registered."""
    catalog = BlueprintCatalog()
    catalog.register(TEXT_UTILITY_BLUEPRINT)
    catalog.register(RESEARCH_NOTES_BLUEPRINT)
    return catalog
