from __future__ import annotations

import unittest

from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, ApplicationIntent
from servicefabric_application_factory_contracts import (
    ApplicationFactoryHandoff,
    EngineeringBlueprint,
    EngineeringLane,
    ModuleTechnologySelection,
    TechnologyProfile,
    UnmetRequirement,
)


class FactoryContractTests(unittest.TestCase):
    def test_profile_is_immutable_and_carries_exact_selection(self) -> None:
        profile = TechnologyProfile(profile_id="profile-1", application_blueprint_id="blueprint-1", application_blueprint_version="1.0.0", module_selections=(ModuleTechnologySelection(module_id="api", primitive="service", kit_reference="fastapi-service@1.0.0", adapter_id="http", runtime_family="python", lifecycle_requirements=("build", "runtime"), provider_role="implementation"),), approved=True)
        with self.assertRaises(Exception):
            profile.approved = False

    def test_blueprint_reuses_agent_run_plan(self) -> None:
        plan = AgentRunPlan(run_id="run-1", intent=ApplicationIntent(intent_id="intent-1", mode="create", objective="Create an API"), tasks=(AgentTask(task_id="api", role="implementation", objective="Create API"),), maximum_parallel_tasks=1)
        blueprint = EngineeringBlueprint(blueprint_id="engineering-1", application_id="app-1", application_blueprint_id="blueprint-1", technology_profile_id="profile-1", agent_run_plan=plan, lanes=(EngineeringLane(lane_id="api", role="implementation", module_ids=("api",), provider_role="implementation"),), integration_lane_id="integration", acceptance_lane_id="acceptance", maximum_parallel_tasks=1)
        self.assertEqual(blueprint.agent_run_plan.run_id, "run-1")

    def test_handoff_carries_structured_unmet_requirement(self) -> None:
        handoff = ApplicationFactoryHandoff(run_id="run-1", application_id="app-1", status="blocked", agent_handoff_ref="runs/run-1", unmet_requirements=(UnmetRequirement(requirement_id="req-1", application_id="app-1", run_id="run-1", required_behavior="Managed database", proposed_scope="platform", urgency="high"),))
        self.assertEqual(handoff.unmet_requirements[0].proposed_scope, "platform")
