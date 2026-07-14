from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for relative in (
    "packages/servicefabric_application_assembly",
    "packages/servicefabric_application_model",
    "packages/servicefabric_blueprints",
    "packages/servicefabric_framework_kits",
    "packages/servicefabric_resource_bindings",
):
    package_root = str(ROOT / relative)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)

from servicefabric_application_assembly import assemble_application
from servicefabric_application_model import DependencyError, ValidationError
from servicefabric_application_model import load_module_definition_from_dict
from servicefabric_blueprints import ApplicationBlueprint, BlueprintModule
from servicefabric_framework_kits import get_default_catalog
from servicefabric_framework_kits.errors import PrimitiveMismatch
from servicefabric_framework_kits.identifiers import parse_kit_reference
from servicefabric_resource_bindings import ResourceBindingRequest


KIT = (
    "fastapi-service @ServiceFabric/portfolio/applications/"
    "revisions/examples.hello-static-1.0.0.json"
)


def module_manifest(
    module_id: str,
    *,
    provides: list[dict[str, str]] | None = None,
    requires: list[str] | None = None,
    resources: list[dict[str, str]] | None = None,
    start_after: list[str] | None = None,
    primitive: str = "service",
) -> dict[str, object]:
    spec: dict[str, object] = {
        "primitive": primitive,
        "kit": KIT,
        "source": f"examples/wave-01/{module_id}",
    }
    if provides:
        spec["provides"] = provides
    required: dict[str, object] = {}
    if requires:
        required["interfaces"] = [{"id": item} for item in requires]
    if resources:
        required["resources"] = resources
    if required:
        spec["requires"] = required
    if start_after:
        spec["lifecycle"] = {"startAfter": start_after}
    return {
        "apiVersion": "servicefabric.local/v1",
        "kind": "ApplicationModule",
        "metadata": {"id": module_id, "version": "0.1.0"},
        "spec": spec,
    }


def wave_blueprint() -> ApplicationBlueprint:
    return ApplicationBlueprint(
        blueprint_id="wave-01-acceptance",
        version="0.1.0",
        title="Wave 01 Acceptance",
        description="Three-module composition used by the Wave-1 integration gate.",
        modules=(
            BlueprintModule.from_manifest(
                module_manifest(
                    "db-adapter",
                    provides=[{"id": "db-client", "type": "python-package"}],
                )
            ),
            BlueprintModule.from_manifest(
                module_manifest(
                    "api",
                    provides=[{"id": "api-http", "type": "http"}],
                    requires=["db-client"],
                    resources=[
                        {
                            "id": "app-db",
                            "type": "postgres",
                            "scope": "application",
                        }
                    ],
                    start_after=["app-db"],
                )
            ),
            BlueprintModule.from_manifest(
                module_manifest("web", requires=["api-http"], start_after=["api"])
            ),
        ),
    )


def serialized_assembly(assembly) -> str:
    payload = {
        "build_order": assembly.build_order,
        "edges": [
            {
                "kind": edge.kind,
                "source": edge.source,
                "target": edge.target,
                "via": edge.via,
            }
            for edge in assembly.edges
        ],
        "interfaces": dict(sorted(assembly.interface_providers.items())),
        "modules": {
            module_id: {
                "depends_on_modules": node.depends_on_modules,
                "depends_on_resources": node.depends_on_resources,
                "provides": node.provides_interfaces,
                "requires": node.requires_interfaces,
            }
            for module_id, node in sorted(assembly.modules_by_id.items())
        },
        "resources": {
            resource_id: {
                "requested_by": resource.requested_by,
                "scope": resource.scope,
                "type": resource.type,
            }
            for resource_id, resource in sorted(assembly.resources_by_id.items())
        },
        "shutdown_order": assembly.shutdown_order,
        "startup_order": assembly.startup_order,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class Wave01AcceptanceJourneyTests(unittest.TestCase):
    def test_modular_composition_loads_and_assembles_deterministically(self) -> None:
        blueprint = wave_blueprint()
        manifests = blueprint.module_manifests()
        modules = tuple(load_module_definition_from_dict(manifest) for manifest in manifests)

        loaded = blueprint.load_modules()
        self.assertEqual([module.module_id for module in loaded], ["db-adapter", "api", "web"])

        catalog = get_default_catalog()
        resolved = [
            catalog.resolve(parse_kit_reference(module.kit))[0].reference.kit_id
            for module in loaded
        ]
        self.assertEqual(resolved, ["fastapi-service", "fastapi-service", "fastapi-service"])
        for module in loaded:
            catalog.validate_module(module)

        assembly = assemble_application(reversed(modules))
        self.assertEqual(assembly.interface_providers, {"api-http": "api", "db-client": "db-adapter"})
        self.assertEqual(assembly.resources_by_id["app-db"].requested_by, ("api",))
        binding_request = ResourceBindingRequest.from_application_request(loaded[1].resources[0])
        self.assertEqual((binding_request.id, binding_request.type), ("app-db", "postgres"))
        self.assertEqual(assembly.build_order, ("db-adapter", "api", "web"))
        self.assertEqual(assembly.startup_order, ("db-adapter", "api", "web"))
        self.assertEqual(assembly.shutdown_order, ("web", "api", "db-adapter"))

        repeat = assemble_application(reversed(tuple(load_module_definition_from_dict(item) for item in manifests)))
        self.assertEqual(serialized_assembly(assembly), serialized_assembly(repeat))

    def test_invalid_dependencies_resources_and_primitives_fail_safely(self) -> None:
        with self.assertRaises(DependencyError):
            assemble_application(
                [
                    load_module_definition_from_dict(
                        module_manifest("api", requires=["missing-interface"])
                    )
                ]
            )

        with self.assertRaises(ValidationError):
            assemble_application(
                [
                    load_module_definition_from_dict(
                        module_manifest(
                            "api",
                            resources=[{"id": "shared-db", "type": "postgres"}],
                        )
                    ),
                    load_module_definition_from_dict(
                        module_manifest(
                            "worker",
                            resources=[{"id": "shared-db", "type": "redis"}],
                        )
                    ),
                ]
            )

        invalid = load_module_definition_from_dict(
            module_manifest("worker", primitive="worker")
        )
        with self.assertRaises(PrimitiveMismatch):
            get_default_catalog().validate_module(invalid)


if __name__ == "__main__":
    unittest.main()
