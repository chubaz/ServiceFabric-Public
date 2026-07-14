"""Unit and conformance tests for the fastapi-service framework kit."""

from __future__ import annotations

import unittest
from pathlib import Path

from servicefabric_application_model import load_module_definition_from_dict
from servicefabric_framework_kits import (
    BuildPlan,
    DependencyPlan,
    HealthPlan,
    KitPlanningContext,
    ProcessPlan,
    get_default_catalog,
    parse_kit_reference,
)


class TestFastAPIServiceKit(unittest.TestCase):
    def setUp(self) -> None:
        self.context = KitPlanningContext(
            workspace_root=Path("/workspace"),
            state_root=Path("/workspace/.servicefabric"),
            artifacts_dir=Path("/workspace/.servicefabric/artifacts"),
            logs_dir=Path("/workspace/.servicefabric/logs"),
        )
        self.module_data = {
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "api-service", "version": "0.1.0"},
            "spec": {
                "primitive": "service",
                "kit": (
                    "fastapi-service @ServiceFabric/portfolio/applications/"
                    "revisions/examples.hello-static-1.0.0.json"
                ),
                "source": "modules/api",
                "lifecycle": {
                    "readiness": {"type": "http", "path": "/health/ready"}
                }
            }
        }

    def test_fastapi_service_adapter_plan_generations(self) -> None:
        mod = load_module_definition_from_dict(self.module_data)
        catalog = get_default_catalog()
        
        ref = parse_kit_reference(mod.kit)
        _, adapter = catalog.resolve(ref)

        # 1. Dependency Plan
        dep_plan = adapter.dependency_plan(mod, self.context)
        self.assertEqual(dep_plan.ecosystem, "python")
        self.assertEqual(dep_plan.manifest_path, "pyproject.toml")
        self.assertEqual(dep_plan.environment_key, "PYTHONPATH")

        # 2. Build Plan
        b_plan = adapter.build_plan(mod, self.context)
        self.assertEqual(b_plan.adapter_id, "python-package")
        self.assertEqual(b_plan.source_directory, "modules/api")
        self.assertEqual(b_plan.output_directory, str(self.context.artifacts_dir))

        # 3. Development Plan (hot-reloading)
        dev_plan = adapter.development_plan(mod, self.context)
        self.assertEqual(dev_plan.adapter_id, "python-asgi")
        self.assertEqual(dev_plan.application_import, "app:app")
        self.assertTrue(dev_plan.reload)
        self.assertEqual(dev_plan.port_binding, "allocated")

        # 4. Runtime Plan (no reload)
        rt_plan = adapter.runtime_plan(mod, self.context)
        self.assertEqual(rt_plan.adapter_id, "python-asgi")
        self.assertEqual(rt_plan.application_import, "app:app")
        self.assertFalse(rt_plan.reload)
        self.assertEqual(rt_plan.port_binding, "allocated")

        # 5. Health Plan
        h_plan = adapter.health_plan(mod, self.context)
        self.assertEqual(h_plan.probe_type, "http")
        self.assertEqual(h_plan.path, "/health/ready")
        self.assertEqual(h_plan.timeout_seconds, 10.0)


if __name__ == "__main__":
    unittest.main()
