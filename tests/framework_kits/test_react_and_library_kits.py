"""Conformance tests for reviewed React and Python library planning."""

from __future__ import annotations

import unittest
from pathlib import Path

from servicefabric_application_model import load_module_definition_from_dict
from servicefabric_framework_kits import (
    KitPlanningContext,
    PythonLibraryPreparationPlan,
    StaticWebRuntimePlan,
    ViteDevelopmentPlan,
    get_default_catalog,
    parse_kit_reference,
)


class TestReactAndLibraryKits(unittest.TestCase):
    def setUp(self) -> None:
        self.context = KitPlanningContext(
            workspace_root=Path("/workspace"),
            state_root=Path("/workspace/.servicefabric"),
            artifacts_dir=Path("/workspace/.servicefabric/artifacts"),
            logs_dir=Path("/workspace/.servicefabric/logs"),
        )

    def _adapter_for(self, module_data: dict):
        module = load_module_definition_from_dict(module_data)
        _, adapter = get_default_catalog().resolve(parse_kit_reference(module.kit))
        return module, adapter

    def test_react_web_plans_are_bounded_and_static_at_runtime(self) -> None:
        module, adapter = self._adapter_for(
            {
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "notes-web", "version": "1.0.0"},
                "spec": {
                    "primitive": "web",
                    "kit": (
                        "react-web @ServiceFabric/portfolio/applications/"
                        "revisions/examples.research-notes-1.0.0.json"
                    ),
                    "source": "modules/web",
                },
            }
        )

        dependencies = adapter.dependency_plan(module, self.context)
        development = adapter.development_plan(module, self.context)
        runtime = adapter.runtime_plan(module, self.context)

        self.assertEqual(dependencies.ecosystem, "node")
        self.assertEqual(dependencies.manifest_path, "package.json")
        self.assertEqual(dependencies.environment_key, "SF_API_BASE_URL")
        self.assertIsInstance(development, ViteDevelopmentPlan)
        self.assertEqual(development.port_binding, "allocated")
        self.assertIsInstance(runtime, StaticWebRuntimePlan)
        self.assertEqual(runtime.assets_directory, str(self.context.artifacts_dir))

    def test_python_library_returns_preparation_not_a_process_plan(self) -> None:
        module, adapter = self._adapter_for(
            {
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": "notes-domain", "version": "1.0.0"},
                "spec": {
                    "primitive": "library",
                    "kit": (
                        "python-library @ServiceFabric/portfolio/applications/"
                        "revisions/examples.research-notes-1.0.0.json"
                    ),
                    "source": "modules/domain",
                },
            }
        )

        preparation = adapter.development_plan(module, self.context)

        self.assertIsInstance(preparation, PythonLibraryPreparationPlan)
        self.assertEqual(preparation.working_directory, "modules/domain")
        self.assertEqual(preparation.test_target, "tests")
        self.assertEqual(adapter.health_plan(module, self.context).probe_type, "none")


if __name__ == "__main__":
    unittest.main()
