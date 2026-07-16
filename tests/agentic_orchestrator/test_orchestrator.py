import unittest

from servicefabric_agentic_contracts import (
    AgentRunPlan,
    AgentTask,
    AgentTaskResult,
    ApplicationIntent,
)
from servicefabric_agentic_orchestrator import ready_tasks


class OrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intent = ApplicationIntent(
            intent_id="intent",
            mode="create",
            objective="build",
        )

    @staticmethod
    def task(task_id: str, *dependencies: str) -> AgentTask:
        return AgentTask(
            task_id=task_id,
            role="implementation",
            objective=f"implement {task_id}",
            dependencies=dependencies,
        )

    def plan(
        self,
        *tasks: AgentTask,
        maximum_parallel_tasks: int = 2,
    ) -> AgentRunPlan:
        return AgentRunPlan(
            run_id="run",
            intent=self.intent,
            tasks=tasks,
            maximum_parallel_tasks=maximum_parallel_tasks,
        )

    def test_parallel_limit_and_plan_order_are_enforced(self) -> None:
        plan = self.plan(
            self.task("one"),
            self.task("two"),
            self.task("three"),
            maximum_parallel_tasks=2,
        )

        self.assertEqual(
            tuple(task.task_id for task in ready_tasks(plan)),
            ("one", "two"),
        )

    def test_dependencies_require_success(self) -> None:
        plan = self.plan(self.task("foundation"), self.task("consumer", "foundation"))

        self.assertEqual(
            tuple(task.task_id for task in ready_tasks(plan)),
            ("foundation",),
        )
        self.assertEqual(
            tuple(
                task.task_id
                for task in ready_tasks(
                    plan,
                    (AgentTaskResult(task_id="foundation", status="success"),),
                )
            ),
            ("consumer",),
        )
        self.assertEqual(
            ready_tasks(
                plan,
                (AgentTaskResult(task_id="foundation", status="failed"),),
            ),
            (),
        )

    def test_in_flight_tasks_reserve_parallel_capacity(self) -> None:
        plan = self.plan(
            self.task("one"),
            self.task("two"),
            self.task("three"),
            maximum_parallel_tasks=2,
        )
        results = (AgentTaskResult(task_id="one", status="running"),)

        self.assertEqual(
            tuple(task.task_id for task in ready_tasks(plan, results)),
            ("two",),
        )

    def test_recorded_pending_task_is_not_dispatched_again(self) -> None:
        plan = self.plan(self.task("one"), self.task("two"))
        results = (AgentTaskResult(task_id="one", status="pending"),)

        self.assertEqual(
            tuple(task.task_id for task in ready_tasks(plan, results)),
            ("two",),
        )

    def test_results_from_another_plan_do_not_consume_capacity(self) -> None:
        plan = self.plan(self.task("one"), maximum_parallel_tasks=1)
        results = (AgentTaskResult(task_id="unrelated", status="running"),)

        self.assertEqual(
            tuple(task.task_id for task in ready_tasks(plan, results)),
            ("one",),
        )

    def test_duplicate_task_ids_are_scheduled_once(self) -> None:
        plan = self.plan(self.task("same"), self.task("same"))

        self.assertEqual(
            tuple(task.task_id for task in ready_tasks(plan)),
            ("same",),
        )
