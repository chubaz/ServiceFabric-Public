from __future__ import annotations

import unittest

from servicefabric_agentic_contracts import ApplicationIntent
from servicefabric_application_factory_contracts import (
    EngineeringLane,
    ModuleTechnologySelection,
    TechnologyProfile,
)
from servicefabric_blueprints.builtins import RESEARCH_NOTES_BLUEPRINT
from servicefabric_engineering_blueprints import (
    BlueprintCompilationError,
    compile_engineering_blueprint,
)


def approved_profile(*, approved: bool = True) -> TechnologyProfile:
    return TechnologyProfile(
        profile_id="research-notes-python-node",
        application_blueprint_id="research-notes",
        application_blueprint_version="0.1.0",
        module_selections=(
            ModuleTechnologySelection(module_id="notes-api", primitive="service", kit_reference="fastapi-service@1.0.0", adapter_id="http", runtime_family="python", provider_role="implementation"),
            ModuleTechnologySelection(module_id="notes-domain", primitive="library", kit_reference="python-library@1.0.0", adapter_id="python", runtime_family="python", provider_role="implementation"),
            ModuleTechnologySelection(module_id="notes-web", primitive="web", kit_reference="react-web@1.0.0", adapter_id="http", runtime_family="node", provider_role="implementation"),
        ),
        approved=approved,
    )


class EngineeringBlueprintCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intent = ApplicationIntent(intent_id="research-notes", application_id="research-notes", mode="create", objective="Build reviewed research notes")

    def test_compiles_disjoint_module_lanes_and_canonical_plan(self) -> None:
        result = compile_engineering_blueprint(self.intent, RESEARCH_NOTES_BLUEPRINT, approved_profile())

        self.assertEqual(result.agent_run_plan.intent, self.intent)
        self.assertEqual(result.integration_lane_id, "application-integration")
        self.assertEqual(result.acceptance_lane_id, "application-assurance")
        self.assertEqual(tuple(task.task_id for task in result.agent_run_plan.tasks), tuple(lane.lane_id for lane in result.lanes))
        paths = [path for lane in result.lanes for path in lane.allowed_paths]
        self.assertEqual(len(paths), len(set(paths)))
        integration = next(lane for lane in result.lanes if lane.integration_owned)
        self.assertEqual(set(integration.dependencies), {"module-notes-api", "module-notes-domain", "module-notes-web"})

    def test_rejects_unapproved_or_incomplete_profile(self) -> None:
        with self.assertRaisesRegex(BlueprintCompilationError, "approved"):
            compile_engineering_blueprint(self.intent, RESEARCH_NOTES_BLUEPRINT, approved_profile(approved=False))

    def test_enforces_hierarchically_disjoint_reviewed_candidate_paths(self) -> None:
        conflicts = (
            ("exact duplicate", "modules/api", "modules/api", ()),
            ("parent then child", "modules/api", "modules/api/routes", ()),
            ("child then parent", "modules/api/routes", "modules/api", ()),
            ("normalized equivalent", "modules//api/./", "modules/api", ()),
            ("dependency does not permit overlap", "modules/api", "modules/api/routes", ("api",)),
            ("forbidden path does not permit overlap", "modules/api", "modules/api/routes", (), ("modules/api",)),
        )
        for case in conflicts:
            name, api_path, web_path, dependencies, *forbidden = case
            with self.subTest(name=name):
                lanes = (
                    EngineeringLane(lane_id="api", role="implementation", allowed_paths=(api_path,), provider_role="implementation"),
                    EngineeringLane(lane_id="web", role="implementation", dependencies=dependencies, allowed_paths=(web_path,), forbidden_paths=forbidden[0] if forbidden else (), provider_role="implementation"),
                    EngineeringLane(lane_id="integration", role="integration", dependencies=("api", "web"), allowed_paths=(".servicefabric/integration",), provider_role="integration", integration_owned=True),
                    EngineeringLane(lane_id="assurance", role="assurance", dependencies=("integration",), allowed_paths=(".servicefabric/assurance",), provider_role="assurance"),
                )
                with self.assertRaisesRegex(BlueprintCompilationError, "overlap"):
                    compile_engineering_blueprint(self.intent, RESEARCH_NOTES_BLUEPRINT, approved_profile(), lanes=lanes)

        with self.subTest(name="integration parent"):
            lanes = (
                EngineeringLane(lane_id="research", role="implementation", allowed_paths=("modules/research",), provider_role="implementation"),
                EngineeringLane(lane_id="integration", role="integration", dependencies=("research",), allowed_paths=("modules",), provider_role="integration", integration_owned=True),
                EngineeringLane(lane_id="assurance", role="assurance", dependencies=("integration",), allowed_paths=(".servicefabric/assurance",), provider_role="assurance"),
            )
            with self.assertRaisesRegex(BlueprintCompilationError, "overlap"):
                compile_engineering_blueprint(self.intent, RESEARCH_NOTES_BLUEPRINT, approved_profile(), lanes=lanes)

        for name, unsafe_path in (
            ("empty path", ""),
            ("absolute path", "/modules/api"),
            ("repository root", "."),
            ("parent traversal", "modules/../api"),
        ):
            with self.subTest(name=name):
                lanes = (
                    EngineeringLane(lane_id="api", role="implementation", allowed_paths=(unsafe_path,), provider_role="implementation"),
                    EngineeringLane(lane_id="integration", role="integration", dependencies=("api",), allowed_paths=("pyproject.toml",), provider_role="integration", integration_owned=True),
                    EngineeringLane(lane_id="assurance", role="assurance", dependencies=("integration",), allowed_paths=("tests/assurance",), provider_role="assurance"),
                )
                with self.assertRaisesRegex(BlueprintCompilationError, "unsafe allowed path"):
                    compile_engineering_blueprint(self.intent, RESEARCH_NOTES_BLUEPRINT, approved_profile(), lanes=lanes)

        with self.subTest(name="similar prefixes are disjoint"):
            lanes = (
                EngineeringLane(lane_id="api", role="implementation", allowed_paths=("modules/api",), provider_role="implementation"),
                EngineeringLane(lane_id="api-client", role="implementation", allowed_paths=("modules/api-client",), provider_role="implementation"),
                EngineeringLane(lane_id="integration", role="integration", dependencies=("api", "api-client"), allowed_paths=("pyproject.toml",), provider_role="integration", integration_owned=True),
                EngineeringLane(lane_id="assurance", role="assurance", dependencies=("integration",), allowed_paths=("tests/assurance",), provider_role="assurance"),
            )
            result = compile_engineering_blueprint(
                self.intent, RESEARCH_NOTES_BLUEPRINT, approved_profile(), lanes=lanes
            )
            self.assertEqual(
                tuple(task.task_id for task in result.agent_run_plan.tasks),
                tuple(lane.lane_id for lane in lanes),
            )


if __name__ == "__main__":
    unittest.main()
