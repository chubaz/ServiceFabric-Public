import unittest

from servicefabric_agentic_contracts import AgentTask, ApplicationIntent
from servicefabric_agentic_planner import PlanValidationError, compile_plan


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.intent = ApplicationIntent(
            intent_id="intent",
            mode="create",
            objective="build",
        )

    def test_default_plan_is_deterministic_and_bounded(self):
        plan = compile_plan(self.intent)

        self.assertEqual(plan.run_id, "run-intent")
        self.assertEqual(plan.tasks[0].task_id, "intent")
        self.assertEqual(plan.tasks[0].allowed_paths, (".",))
        self.assertEqual(plan.tasks[0].required_context, ("AGENTS.md",))

    def test_compiles_parallel_ready_dependency_graph(self):
        foundation = AgentTask(
            task_id="foundation",
            role="implementation",
            objective="build foundation",
            allowed_paths=("packages/foundation",),
        )
        adapter = AgentTask(
            task_id="adapter",
            role="implementation",
            objective="build adapter",
            dependencies=("foundation",),
            allowed_paths=("packages/adapter",),
            forbidden_paths=("packages/contracts",),
        )

        plan = compile_plan(
            self.intent,
            run_id="custom-run",
            maximum_parallel_tasks=2,
            tasks=(foundation, adapter),
        )

        self.assertEqual(plan.run_id, "custom-run")
        self.assertEqual(plan.tasks, (foundation, adapter))
        self.assertEqual(plan.maximum_parallel_tasks, 2)

    def test_rejects_empty_task_graph(self):
        with self.assertRaisesRegex(PlanValidationError, "at least one task"):
            compile_plan(self.intent, tasks=())

    def test_rejects_duplicate_task_ids(self):
        task = AgentTask(
            task_id="duplicate",
            role="implementation",
            objective="build",
            allowed_paths=("packages/one",),
        )

        with self.assertRaisesRegex(PlanValidationError, "duplicate task_id"):
            compile_plan(self.intent, tasks=(task, task))

    def test_rejects_missing_task_bounds(self):
        task = AgentTask(
            task_id="unbounded",
            role="implementation",
            objective="build",
        )

        with self.assertRaisesRegex(PlanValidationError, "declare allowed_paths"):
            compile_plan(self.intent, tasks=(task,))

    def test_rejects_parent_path_traversal(self):
        task = AgentTask(
            task_id="unsafe",
            role="implementation",
            objective="build",
            allowed_paths=("packages/../contracts",),
        )

        with self.assertRaisesRegex(PlanValidationError, "unsafe allowed_paths"):
            compile_plan(self.intent, tasks=(task,))

    def test_rejects_unknown_dependency(self):
        task = AgentTask(
            task_id="adapter",
            role="implementation",
            objective="build adapter",
            dependencies=("missing",),
            allowed_paths=("packages/adapter",),
        )

        with self.assertRaisesRegex(PlanValidationError, "unknown dependencies: missing"):
            compile_plan(self.intent, tasks=(task,))

    def test_rejects_dependency_cycle(self):
        first = AgentTask(
            task_id="first",
            role="implementation",
            objective="first",
            dependencies=("second",),
            allowed_paths=("packages/first",),
        )
        second = AgentTask(
            task_id="second",
            role="implementation",
            objective="second",
            dependencies=("first",),
            allowed_paths=("packages/second",),
        )

        with self.assertRaisesRegex(PlanValidationError, "dependency cycle"):
            compile_plan(self.intent, tasks=(first, second))


if __name__ == "__main__":
    unittest.main()
