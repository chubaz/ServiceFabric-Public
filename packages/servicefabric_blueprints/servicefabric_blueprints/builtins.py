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
    description="Reviewed domain library, FastAPI API, and React web modules with a local SQLite binding.",
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
                                "type": "sqlite",
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
        BlueprintModule.from_manifest(
            {
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "notes-domain", "version": "0.2.0"},
                "spec": {
                    "primitive": "library",
                    "kit": "python-library @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                    "source": "examples/research-notes/domain",
                    "provides": [{"id": "notes-domain", "type": "python-library"}],
                    "lifecycle": {"shutdown": {"timeoutSeconds": 5}},
                    "resourceExpectations": {"memoryMiB": 64, "cpuCores": 0.1},
                },
            }
        ),
        BlueprintModule.from_manifest(
            {
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "notes-web", "version": "0.2.0"},
                "spec": {
                    "primitive": "web",
                    "kit": "react-web @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                    "source": "examples/research-notes/web",
                    "provides": [{"id": "notes-web", "type": "http", "protocol": "http"}],
                    "requires": {"interfaces": [{"id": "notes-api"}]},
                    "lifecycle": {
                        "startAfter": ["notes-api"],
                        "readiness": {"type": "http", "path": "/"},
                        "shutdown": {"timeoutSeconds": 10},
                    },
                    "resourceExpectations": {"memoryMiB": 128, "cpuCores": 0.1},
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
