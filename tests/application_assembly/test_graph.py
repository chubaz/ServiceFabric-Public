from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "servicefabric_application_assembly"))
sys.path.insert(0, str(ROOT / "packages" / "servicefabric_application_model"))

from servicefabric_application_assembly import assemble_application
from servicefabric_application_model import DependencyError, ValidationError
from servicefabric_application_model import load_module_definition_from_dict


KIT = "fastapi-service @ServiceFabric/portfolio/applications/revisions/examples.hello-static-1.0.0.json"


def module_data(
    module_id: str,
    primitive: str = "service",
    provides: list[dict[str, str]] | None = None,
    interfaces: list[str] | None = None,
    resources: list[dict[str, str]] | None = None,
    start_after: list[str] | None = None,
) -> dict[str, object]:
    spec: dict[str, object] = {
        "primitive": primitive,
        "kit": KIT,
        "source": f"modules/{module_id}",
    }
    if provides is not None:
        spec["provides"] = provides
    requires: dict[str, object] = {}
    if interfaces is not None:
        requires["interfaces"] = [{"id": item} for item in interfaces]
    if resources is not None:
        requires["resources"] = resources
    if requires:
        spec["requires"] = requires
    if start_after is not None:
        spec["lifecycle"] = {"startAfter": start_after}

    return {
        "apiVersion": "servicefabric.local/v1",
        "kind": "ApplicationModule",
        "metadata": {"id": module_id, "version": "0.1.0"},
        "spec": spec,
    }


def load_module(data: dict[str, object]):
    return load_module_definition_from_dict(data)


class TestApplicationAssembly(unittest.TestCase):
    def test_assembles_interfaces_resources_and_lifecycle_edges(self) -> None:
        domain = load_module(
            module_data(
                "domain",
                primitive="library",
                provides=[{"id": "domain-pkg", "type": "python-package"}],
            )
        )
        api = load_module(
            module_data(
                "api",
                provides=[{"id": "api-http", "type": "http"}],
                interfaces=["domain-pkg"],
                resources=[{"id": "primary-store", "type": "relational-database"}],
                start_after=["primary-store"],
            )
        )
        web = load_module(
            module_data("web", primitive="web", interfaces=["api-http"], start_after=["api"])
        )

        assembly = assemble_application([web, api, domain])

        self.assertEqual(assembly.build_order, ("domain", "api", "web"))
        self.assertEqual(assembly.startup_order, ("domain", "api", "web"))
        self.assertEqual(assembly.shutdown_order, ("web", "api", "domain"))
        self.assertEqual(
            assembly.interface_providers,
            {"domain-pkg": "domain", "api-http": "api"},
        )
        self.assertEqual(
            assembly.resources_by_id["primary-store"].requested_by,
            ("api",),
        )
        self.assertEqual(
            assembly.modules_by_id["api"].depends_on_resources,
            ("primary-store",),
        )
        self.assertIn(
            ("domain", "api", "interface", "domain-pkg"),
            {(edge.source, edge.target, edge.kind, edge.via) for edge in assembly.edges},
        )
        self.assertIn(
            ("primary-store", "api", "lifecycle", "primary-store"),
            {(edge.source, edge.target, edge.kind, edge.via) for edge in assembly.edges},
        )

    def test_merges_compatible_resource_requests(self) -> None:
        api = load_module(
            module_data(
                "api",
                resources=[{"id": "primary-store", "type": "relational-database"}],
            )
        )
        worker = load_module(
            module_data(
                "worker",
                primitive="worker",
                resources=[{"id": "primary-store", "type": "relational-database"}],
            )
        )

        assembly = assemble_application([worker, api])

        self.assertEqual(
            assembly.resources_by_id["primary-store"].requested_by,
            ("api", "worker"),
        )

    def test_rejects_conflicting_resource_definitions(self) -> None:
        api = load_module(
            module_data(
                "api",
                resources=[{"id": "shared-binding", "type": "relational-database"}],
            )
        )
        worker = load_module(
            module_data(
                "worker",
                primitive="worker",
                resources=[{"id": "shared-binding", "type": "message-queue"}],
            )
        )

        with self.assertRaisesRegex(ValidationError, "conflicting definitions"):
            assemble_application([api, worker])

    def test_rejects_resource_and_module_id_collision(self) -> None:
        store = load_module(module_data("store"))
        api = load_module(
            module_data(
                "api",
                resources=[{"id": "store", "type": "relational-database"}],
                start_after=["store"],
            )
        )

        with self.assertRaisesRegex(ValidationError, "collide with module"):
            assemble_application([store, api])

    def test_delegates_missing_interface_detection_to_model_graph_validation(self) -> None:
        api = load_module(module_data("api", interfaces=["missing-pkg"]))

        with self.assertRaisesRegex(DependencyError, "requires interface"):
            assemble_application([api])


if __name__ == "__main__":
    unittest.main()
