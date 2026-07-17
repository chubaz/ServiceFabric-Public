from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
for source in reversed((
    ROOT / "packages" / "servicefabric_contracts" / "src",
    ROOT / "packages" / "servicefabric_agentic_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_contracts" / "src",
    ROOT / "packages" / "servicefabric_langgraph_orchestration" / "src",
)):
    sys.path.insert(0, str(source))

from servicefabric_agent_provider_contracts import ProviderPolicy
from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, ApplicationIntent
from servicefabric_langgraph_orchestration import LangGraphOrchestrator


class LangGraphOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = LangGraphOrchestrator()
        self.policy = ProviderPolicy(
            default_provider="codex",
            role_overrides={"review": "claude"},
            maximum_parallel_per_provider=1,
            timeout_seconds=90,
            maximum_turns=4,
        )

    def test_compiles_dependency_ordered_provider_requests(self) -> None:
        plan = AgentRunPlan(
            run_id="run-1",
            intent=ApplicationIntent(intent_id="intent-1", mode="create", objective="Create a service."),
            maximum_parallel_tasks=2,
            tasks=(
                AgentTask(task_id="design", role="design", objective="Design the change.", allowed_paths=("docs/",)),
                AgentTask(task_id="review", role="review", objective="Review the design.", dependencies=("design",)),
                AgentTask(task_id="implement", role="implementation", objective="Implement the change.", dependencies=("design",)),
            ),
        )

        batches = self.orchestrator.compile(plan, self.policy, repository="/workspace", environment_names=("CI",))

        self.assertEqual([[request.task_id for request in batch] for batch in batches], [["design"], ["review", "implement"]])
        self.assertEqual(batches[1][0].provider_id, "claude")
        self.assertEqual(batches[1][1].provider_id, "codex")
        self.assertEqual(batches[0][0].timeout_seconds, 90)
        self.assertEqual(batches[0][0].maximum_turns, 4)
        self.assertEqual(batches[0][0].environment_names, ("CI",))
        self.assertIn("Allowed paths:\n- docs/", batches[0][0].prompt)

    def test_splits_independent_tasks_to_respect_provider_limit(self) -> None:
        plan = self._plan(
            AgentTask(task_id="one", role="implementation", objective="One."),
            AgentTask(task_id="two", role="implementation", objective="Two."),
            AgentTask(task_id="three", role="review", objective="Three."),
        )

        batches = self.orchestrator.compile(plan, self.policy, repository="/workspace")

        self.assertEqual([[request.task_id for request in batch] for batch in batches], [["one", "three"], ["two"]])

    def test_rejects_unknown_dependencies_and_cycles(self) -> None:
        unknown = self._plan(AgentTask(task_id="one", role="implementation", objective="One.", dependencies=("missing",)))
        with self.assertRaisesRegex(ValueError, "unknown task dependencies"):
            self.orchestrator.compile(unknown, self.policy, repository="/workspace")

        cycle = self._plan(
            AgentTask(task_id="one", role="implementation", objective="One.", dependencies=("two",)),
            AgentTask(task_id="two", role="implementation", objective="Two.", dependencies=("one",)),
        )
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            self.orchestrator.compile(cycle, self.policy, repository="/workspace")

    @staticmethod
    def _plan(*tasks: AgentTask) -> AgentRunPlan:
        return AgentRunPlan(
            run_id="run-1",
            intent=ApplicationIntent(intent_id="intent-1", mode="create", objective="Create a service."),
            tasks=tasks,
            maximum_parallel_tasks=2,
        )
