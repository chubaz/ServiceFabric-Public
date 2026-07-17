from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
for source in reversed((
    ROOT / "packages" / "servicefabric_contracts" / "src",
    ROOT / "packages" / "servicefabric_agentic_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_harness" / "src",
    ROOT / "packages" / "servicefabric_agentic_orchestrator" / "src",
    ROOT / "packages" / "servicefabric_agentic_run_store" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_contracts" / "src",
    ROOT / "packages" / "servicefabric_langgraph_orchestration" / "src",
)):
    sys.path.insert(0, str(source))

from servicefabric_agent_harness import CodexPromptHarness
from servicefabric_agent_provider_contracts import ProviderExecutionRequest, ProviderPolicy
from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, AgentTaskResult, ApplicationIntent
from servicefabric_agentic_run_store import FileRunStore
from servicefabric_langgraph_orchestration import LangGraphOrchestrator


class LangGraphOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.harness = CodexPromptHarness()
        self.orchestrator = LangGraphOrchestrator(self.harness)
        self.policy = ProviderPolicy(
            default_provider="codex",
            role_overrides={"review": "claude"},
            maximum_parallel_per_provider=1,
            timeout_seconds=90,
            maximum_turns=4,
        )

    def test_uses_the_exact_wave_7_task_pack_prompt_for_ready_tasks(self) -> None:
        plan = AgentRunPlan(
            run_id="run-1",
            intent=ApplicationIntent(intent_id="intent-1", mode="create", objective="Create a service."),
            maximum_parallel_tasks=3,
            tasks=(
                AgentTask(task_id="completed", role="design", objective="Completed."),
                AgentTask(task_id="running", role="implementation", objective="Already running."),
                AgentTask(task_id="pending", role="implementation", objective="Already pending."),
                AgentTask(task_id="review", role="review", objective="Review the completed task.", dependencies=("completed",)),
            ),
        )
        store = self._store_with(
            plan,
            AgentTaskResult(task_id="completed", status="success"),
            AgentTaskResult(task_id="running", status="running"),
            AgentTaskResult(task_id="pending", status="pending"),
        )
        before = (store.root / "run-1.json").read_bytes()

        batches = self.orchestrator.compile(plan, self.policy, store, repository="/workspace", environment_names=("CI",))

        self.assertEqual([[request.task_id for request in batch] for batch in batches], [["review"]])
        request = batches[0][0]
        task_pack = self.harness.prepare_task(plan.tasks[3], "/workspace")
        self.assertEqual(request.task_id, task_pack["task_id"])
        self.assertEqual(request.repository, task_pack["repository"])
        expected_prompt = ProviderExecutionRequest(
            run_id=plan.run_id,
            task_id=task_pack["task_id"],
            provider_id="codex",
            repository=task_pack["repository"],
            prompt=task_pack["prompt"],
            timeout_seconds=self.policy.timeout_seconds,
        ).prompt
        self.assertEqual(request.prompt, expected_prompt)
        self.assertEqual(request.provider_id, "claude")
        self.assertEqual(request.timeout_seconds, 90)
        self.assertEqual(request.maximum_turns, 4)
        self.assertEqual(request.environment_names, ("CI",))
        self.assertEqual((store.root / "run-1.json").read_bytes(), before)

    def test_batches_only_ready_tasks_within_provider_policy_limit(self) -> None:
        plan = self._plan(
            AgentTask(task_id="one", role="implementation", objective="One."),
            AgentTask(task_id="two", role="implementation", objective="Two."),
            AgentTask(task_id="three", role="review", objective="Three."),
        )
        store = self._store_with(plan)

        batches = self.orchestrator.compile(plan, self.policy, store, repository="/workspace")

        self.assertEqual([[request.task_id for request in batch] for batch in batches], [["one"], ["two"]])

    @staticmethod
    def _plan(*tasks: AgentTask) -> AgentRunPlan:
        return AgentRunPlan(
            run_id="run-1",
            intent=ApplicationIntent(intent_id="intent-1", mode="create", objective="Create a service."),
            tasks=tasks,
            maximum_parallel_tasks=2,
        )

    @staticmethod
    def _store_with(plan: AgentRunPlan, *results: AgentTaskResult) -> FileRunStore:
        root = Path(tempfile.mkdtemp())
        store = FileRunStore(root)
        store.save_plan(plan)
        for result in results:
            store.record_result(plan.run_id, result)
        return store
