"""Unit and integration tests for kit planning and plan generation safety."""

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


class TestPlanGeneration(unittest.TestCase):
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
            "metadata": {"id": "notes-api", "version": "1.0.0"},
            "spec": {
                "primitive": "service",
                "kit": (
                    "fastapi-service @ServiceFabric/portfolio/applications/"
                    "revisions/examples.hello-static-1.0.0.json"
                ),
                "source": "modules/api",
            }
        }

    def test_plan_contains_no_workspace_specific_absolute_paths_prematurely(self) -> None:
        # Build plan without context must contain only relative source paths
        # context only specifies target destination directories.
        mod = load_module_definition_from_dict(self.module_data)
        catalog = get_default_catalog()
        
        ref = parse_kit_reference(mod.kit)
        _, adapter = catalog.resolve(ref)
        
        b_plan = adapter.build_plan(mod, self.context)
        self.assertEqual(b_plan.source_directory, "modules/api")
        # Ensure it contains context artifacts directory (not hardcoded)
        self.assertEqual(b_plan.output_directory, str(self.context.artifacts_dir))

    def test_equivalent_input_produces_equivalent_plans(self) -> None:
        mod1 = load_module_definition_from_dict(self.module_data)
        mod2 = load_module_definition_from_dict(self.module_data)

        catalog = get_default_catalog()
        ref = parse_kit_reference(mod1.kit)
        _, adapter = catalog.resolve(ref)

        dev_plan1 = adapter.development_plan(mod1, self.context)
        dev_plan2 = adapter.development_plan(mod2, self.context)

        # Confirm exact equivalency
        self.assertEqual(dev_plan1, dev_plan2)


if __name__ == "__main__":
    unittest.main()
