"""Built-in reviewed application blueprints."""

from __future__ import annotations

from servicefabric_blueprints.catalog import BlueprintCatalog
from servicefabric_blueprints.definitions import ApplicationBlueprint, BlueprintFile, BlueprintModule
from servicefabric_capability_authoring import research_notes_declarations

FASTAPI_SERVICE_KIT = (
    "fastapi-service @ServiceFabric/portfolio/applications/"
    "revisions/examples.hello-static-1.0.0.json"
)


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
        for path, document in sorted(research_notes_declarations().items())
    ),
)


def create_default_blueprint_catalog() -> BlueprintCatalog:
    """Creates a catalog with all built-in reviewed blueprints registered."""
    catalog = BlueprintCatalog()
    catalog.register(TEXT_UTILITY_BLUEPRINT)
    catalog.register(RESEARCH_NOTES_BLUEPRINT)
    return catalog
