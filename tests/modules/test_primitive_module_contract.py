"""Acceptance and unit tests for the AP-00A Primitive and Module Contract (Hardened)."""

from __future__ import annotations

import unittest
from pathlib import Path

from servicefabric_application_model import (
    DependencyError,
    InvalidModuleDefinition,
    InvalidPrimitive,
    LifecycleConfig,
    ModuleDefinition,
    ProvidedInterface,
    ReadinessProbe,
    RequiredInterface,
    ResourceExpectations,
    ResourceRequest,
    ShutdownConfig,
    ValidationError,
    load_module_definition_from_dict,
    validate_module_graph,
    validate_primitive,
)


class TestPrimitiveModuleContract(unittest.TestCase):
    def test_valid_primitives_succeed(self) -> None:
        valid_primitives = ["service", "web", "worker", "job", "library"]
        for prim in valid_primitives:
            self.assertEqual(validate_primitive(prim), prim)

    def test_invalid_primitives_raise_error(self) -> None:
        invalid_primitives = ["api-service", "data-api", "admin-api", "static-web-app", ""]
        for prim in invalid_primitives:
            with self.assertRaises(InvalidPrimitive):
                validate_primitive(prim)

    def test_parses_module_manifest_successfully(self) -> None:
        manifest_data = {
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {
                "id": "api",
                "version": "1.2.3",
            },
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                "source": "modules/api",
                "provides": [
                    {
                        "id": "notes-http",
                        "type": "http",
                        "protocol": "http",
                        "contract": "openapi.yaml",
                    }
                ],
                "requires": {
                    "interfaces": [
                        {"id": "notes-domain"}
                    ],
                    "resources": [
                        {
                            "id": "primary-store",
                            "type": "relational-database",
                            "scope": "application",
                        }
                    ]
                },
                "lifecycle": {
                    "startAfter": ["primary-store"],
                    "readiness": {
                        "type": "http",
                        "path": "/health/ready",
                        "port": 8000,
                    },
                    "shutdown": {
                        "timeoutSeconds": 15,
                    }
                },
                "resourceExpectations": {
                    "memoryMiB": 256,
                    "cpuCores": 0.25
                }
            }
        }

        mod = load_module_definition_from_dict(manifest_data)
        
        self.assertEqual(mod.module_id, "api")
        self.assertEqual(mod.version, "1.2.3")
        self.assertEqual(mod.primitive, "service")
        self.assertEqual(mod.kit, "fastapi-service @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json")
        self.assertEqual(mod.source, "modules/api")

        # Verify provided interfaces
        self.assertEqual(len(mod.provides_interfaces), 1)
        self.assertEqual(
            mod.provides_interfaces[0],
            ProvidedInterface(id="notes-http", type="http", protocol="http", contract="openapi.yaml")
        )

        # Verify required interfaces
        self.assertEqual(len(mod.requires_interfaces), 1)
        self.assertEqual(mod.requires_interfaces[0], RequiredInterface(id="notes-domain"))

        # Verify resource requests (without needing concrete connection details)
        self.assertEqual(len(mod.resources), 1)
        self.assertEqual(
            mod.resources[0],
            ResourceRequest(id="primary-store", type="relational-database", scope="application")
        )

        # Verify lifecycle and readiness/health validation
        self.assertEqual(mod.lifecycle.start_after, ("primary-store",))
        self.assertEqual(mod.lifecycle.readiness, ReadinessProbe(type="http", path="/health/ready", port=8000))
        self.assertEqual(mod.lifecycle.shutdown, ShutdownConfig(timeout_seconds=15))

        # Verify resourceExpectations
        self.assertIsNotNone(mod.resource_expectations)
        self.assertEqual(mod.resource_expectations.memory_mib, 256)
        self.assertEqual(mod.resource_expectations.cpu_cores, 0.25)

    def test_strict_manifest_validation_failures(self) -> None:
        # 1. Unsupported root field
        with self.assertRaises(InvalidModuleDefinition):
            load_module_definition_from_dict({
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "api"},
                "spec": {"primitive": "service", "kit": "fastapi-service @ServiceFabric/p"},
                "extraField": "forbidden",
            })

        # 2. Malformed version format
        with self.assertRaises(InvalidModuleDefinition):
            load_module_definition_from_dict({
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "api", "version": "invalid-semver"},
                "spec": {"primitive": "service", "kit": "fastapi-service @ServiceFabric/p"},
            })

        # 3. Path safety violation (escaping path traversal)
        with self.assertRaises(InvalidModuleDefinition):
            load_module_definition_from_dict({
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "api"},
                "spec": {
                    "primitive": "service",
                    "kit": "fastapi-service @ServiceFabric/p",
                    "source": "../../escaped",
                },
            })

        # 4. Missing required resource type
        with self.assertRaises(InvalidModuleDefinition):
            load_module_definition_from_dict({
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "api"},
                "spec": {
                    "primitive": "service",
                    "kit": "fastapi-service @ServiceFabric/p",
                    "source": "modules/api",
                    "requires": {
                        "resources": [{"id": "no-type"}]
                    }
                },
            })

    def test_complete_research_notes_module_graph_parses_successfully(self) -> None:
        # Module 1: shared domain library (provides domain package interface)
        domain = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "domain", "version": "0.1.0"},
            "spec": {
                "primitive": "library",
                "kit": "python-library @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                "source": "modules/domain",
                "provides": [
                    {"id": "notes-domain-pkg", "type": "python-package"}
                ]
            }
        })

        # Module 2: FastAPI service (requires domain package, provides API interface, requests database resource)
        api = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "api", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                "source": "modules/api",
                "provides": [
                    {"id": "notes-api-http", "type": "http"}
                ],
                "requires": {
                    "interfaces": [{"id": "notes-domain-pkg"}],
                    "resources": [{"id": "primary-store", "type": "relational-database"}]
                },
                "lifecycle": {
                    "startAfter": ["primary-store"],
                    "readiness": {"type": "http", "path": "/health/ready"}
                }
            }
        })

        # Module 3: React web frontend (requires API http interface)
        frontend = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "frontend", "version": "0.1.0"},
            "spec": {
                "primitive": "web",
                "kit": "react-web @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                "source": "modules/frontend",
                "requires": {
                    "interfaces": [{"id": "notes-api-http"}]
                }
            }
        })

        # Module 4: Background worker (requires domain package, requests queue resource)
        worker = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "processor", "version": "0.1.0"},
            "spec": {
                "primitive": "worker",
                "kit": "python-worker @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                "source": "modules/processor",
                "requires": {
                    "interfaces": [{"id": "notes-domain-pkg"}],
                    "resources": [{"id": "jobs-queue", "type": "message-queue"}]
                }
            }
        })

        # Module 5: Discrete importer job (requests primary-store database)
        job = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "daily-import", "version": "0.1.0"},
            "spec": {
                "primitive": "job",
                "kit": "python-job @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json",
                "source": "modules/daily-import",
                "requires": {
                    "resources": [{"id": "primary-store", "type": "relational-database"}]
                }
            }
        })

        # Verify that the complete 5-node modular graph validates beautifully!
        modules_graph = [domain, api, frontend, worker, job]
        graph = validate_module_graph(modules_graph)

        # Verify deterministic topological dependency_order (alphabetical when tie)
        # daily-import and domain have 0 in-degree initially. alphabetical: daily-import first, then domain
        self.assertEqual(graph.dependency_order[0], "daily-import")
        self.assertEqual(graph.dependency_order[1], "domain")
        # After resolving domain, api and processor have 0 in-degree. alphabetical: api first, then processor
        self.assertEqual(graph.dependency_order[2], "api")
        # After resolving api, frontend has 0 in-degree.
        # Queue contains frontend and processor. Alphabetical sorting puts frontend before processor!
        self.assertEqual(graph.dependency_order[3], "frontend")
        self.assertEqual(graph.dependency_order[4], "processor")

        # Verify shutdown order is exact reverse
        self.assertEqual(graph.shutdown_order, ("processor", "frontend", "api", "domain", "daily-import"))

    def test_duplicate_interface_providers_raise_collision_error(self) -> None:
        m1 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-1", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/p",
                "source": "modules/m1",
                "provides": [{"id": "colliding-interface", "type": "http"}]
            }
        })
        m2 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-2", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/p",
                "source": "modules/m2",
                "provides": [{"id": "colliding-interface", "type": "http"}]
            }
        })

        with self.assertRaisesRegex(ValidationError, "Collision: both module 'module-2' and module 'module-1'"):
            validate_module_graph([m1, m2])

    def test_duplicate_local_interface_declaration_raises_error(self) -> None:
        m1 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-1", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/p",
                "source": "modules/m1",
                "provides": [
                    {"id": "duplicate-interface", "type": "http"},
                    {"id": "duplicate-interface", "type": "http"}
                ]
            }
        })

        with self.assertRaisesRegex(ValidationError, "declares duplicate provided interface"):
            validate_module_graph([m1])

    def test_unknown_lifecycle_startup_target_raises_error(self) -> None:
        m1 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-1", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/p",
                "source": "modules/m1",
                "lifecycle": {
                    "startAfter": ["unknown-module-id"]
                }
            }
        })

        with self.assertRaisesRegex(DependencyError, "declares 'startAfter' dependency on unknown module or resource ID"):
            validate_module_graph([m1])

    def test_self_dependency_raises_circular_error(self) -> None:
        m1 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-1", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/p",
                "source": "modules/m1",
                "lifecycle": {
                    "startAfter": ["module-1"]
                }
            }
        })

        with self.assertRaisesRegex(DependencyError, "cannot declare a lifecycle dependency on itself"):
            validate_module_graph([m1])

    def test_source_directory_collisions_raise_error(self) -> None:
        m1 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-1", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/p",
                "source": "modules/same"
            }
        })
        m2 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-2", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service @ServiceFabric/p",
                "source": "modules/same"
            }
        })

        with self.assertRaisesRegex(ValidationError, "Collision: both module 'module-2' and module 'module-1' attempt to use the identical source directory"):
            validate_module_graph([m1, m2])


if __name__ == "__main__":
    unittest.main()
