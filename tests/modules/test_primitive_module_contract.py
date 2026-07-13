"""Acceptance and unit tests for the AP-00A Primitive and Module Contract."""

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
                "kit": "fastapi-service",
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
                }
            }
        }

        mod = load_module_definition_from_dict(manifest_data)
        
        self.assertEqual(mod.module_id, "api")
        self.assertEqual(mod.version, "1.2.3")
        self.assertEqual(mod.primitive, "service")
        self.assertEqual(mod.kit, "fastapi-service")
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

    def test_manifest_validation_failures(self) -> None:
        # 1. Missing apiVersion
        with self.assertRaises(InvalidModuleDefinition):
            load_module_definition_from_dict({"kind": "ApplicationModule"})

        # 2. Missing kind
        with self.assertRaises(InvalidModuleDefinition):
            load_module_definition_from_dict({"apiVersion": "servicefabric.local/v1"})

        # 3. Missing metadata.id
        with self.assertRaises(InvalidModuleDefinition):
            load_module_definition_from_dict({
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"version": "0.1.0"},
            })

    def test_complete_research_notes_module_graph_parses_successfully(self) -> None:
        # Module 1: shared domain library (provides domain package interface)
        domain = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "domain", "version": "0.1.0"},
            "spec": {
                "primitive": "library",
                "kit": "python-library",
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
                "kit": "fastapi-service",
                "source": "modules/api",
                "provides": [
                    {"id": "notes-api-http", "type": "http"}
                ],
                "requires": {
                    "interfaces": ["notes-domain-pkg"],
                    "resources": ["primary-store"]
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
                "kit": "react-web",
                "source": "modules/frontend",
                "requires": {
                    "interfaces": ["notes-api-http"]
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
                "kit": "python-worker",
                "source": "modules/processor",
                "requires": {
                    "interfaces": ["notes-domain-pkg"],
                    "resources": ["jobs-queue"]
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
                "kit": "python-job",
                "source": "modules/daily-import",
                "requires": {
                    "resources": ["primary-store"]
                }
            }
        })

        # Verify that the complete 5-node modular graph validates beautifully!
        modules_graph = [domain, api, frontend, worker, job]
        validate_module_graph(modules_graph)

    def test_unresolved_dependencies_fail_safely(self) -> None:
        # Module requires an interface that is not provided by any other module
        api = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "api", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service",
                "source": "modules/api",
                "requires": {
                    "interfaces": ["non-existent-interface"]
                }
            }
        })

        with self.assertRaises(DependencyError):
            validate_module_graph([api])

    def test_duplicate_module_identities_fail_safely(self) -> None:
        m1 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "api", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service",
                "source": "modules/api"
            }
        })
        m2 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "api", "version": "0.2.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service",
                "source": "modules/api2"
            }
        })

        with self.assertRaises(ValidationError):
            validate_module_graph([m1, m2])

    def test_dependency_cycles_fail_safely(self) -> None:
        # m1 requires m2 interface, m2 requires m1 interface
        m1 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-1", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service",
                "source": "modules/m1",
                "provides": [{"id": "m1-interface", "type": "http"}],
                "requires": {"interfaces": ["m2-interface"]}
            }
        })
        m2 = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "module-2", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": "fastapi-service",
                "source": "modules/m2",
                "provides": [{"id": "m2-interface", "type": "http"}],
                "requires": {"interfaces": ["m1-interface"]}
            }
        })

        with self.assertRaises(DependencyError):
            validate_module_graph([m1, m2])


if __name__ == "__main__":
    unittest.main()
