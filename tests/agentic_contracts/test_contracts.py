import unittest

from pydantic import ValidationError

from servicefabric_agentic_contracts import AgentTask, ApplicationIntent


class AgenticContractTests(unittest.TestCase):
    def test_intent_is_immutable_and_strict(self) -> None:
        intent = ApplicationIntent(intent_id="intent", mode="create", objective="Build")
        with self.assertRaises(ValidationError):
            ApplicationIntent(intent_id="intent", mode="create", objective="Build", extra="no")
        with self.assertRaises(ValidationError):
            intent.objective = "Changed"  # type: ignore[misc]

    def test_task_uses_deterministic_tuples(self) -> None:
        task = AgentTask(task_id="task", role="builder", objective="Build", dependencies=("base",))
        self.assertEqual(task.dependencies, ("base",))
