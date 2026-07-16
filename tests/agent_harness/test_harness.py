from pathlib import Path
import tempfile
import unittest

from servicefabric_agent_harness import CodexPromptHarness
from servicefabric_agentic_contracts import AgentTask


class HarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = AgentTask(
            task_id="task",
            role="implementer",
            objective="Implement the bounded change",
            dependencies=("contracts",),
            allowed_paths=("src", "tests"),
            forbidden_paths=("contracts",),
            required_context=("AGENTS.md",),
            expected_outputs=("implementation", "evidence"),
            verification_commands=("python3 -m unittest",),
        )

    def test_render_has_all_task_boundaries(self) -> None:
        prompt = CodexPromptHarness().render_task(self.task)

        self.assertIn("Task: task", prompt)
        self.assertIn("Role: implementer", prompt)
        self.assertIn("Objective: Implement the bounded change", prompt)
        self.assertIn("Dependencies: contracts", prompt)
        self.assertIn("Allowed paths: src, tests", prompt)
        self.assertIn("Forbidden paths: contracts", prompt)
        self.assertIn("Required context: AGENTS.md", prompt)
        self.assertIn("Expected outputs: implementation, evidence", prompt)
        self.assertIn("Verification: python3 -m unittest", prompt)
        self.assertTrue(prompt.endswith("\n"))

    def test_render_makes_empty_boundaries_explicit(self) -> None:
        task = AgentTask(task_id="task", role="role", objective="do")

        prompt = CodexPromptHarness().render_task(task)

        self.assertIn("Allowed paths: (none)", prompt)
        self.assertIn("Forbidden paths: (none)", prompt)

    def test_prepare_returns_resolved_repository_and_prompt(self) -> None:
        harness = CodexPromptHarness()
        with tempfile.TemporaryDirectory() as repository:
            prepared = harness.prepare_task(self.task, repository)

            self.assertEqual(prepared["task_id"], "task")
            self.assertEqual(prepared["repository"], str(Path(repository).resolve()))
            self.assertEqual(prepared["prompt"], harness.render_task(self.task))
            self.assertEqual(harness.collect_result("task").status, "pending")

    def test_launch_is_provider_neutral_and_tracks_pending_state(self) -> None:
        harness = CodexPromptHarness()

        reference = harness.launch_task(self.task)

        self.assertEqual(reference, "prepared:task")
        self.assertEqual(harness.collect_result("task").status, "pending")

    def test_cancel_records_cancelled_result(self) -> None:
        harness = CodexPromptHarness()
        harness.launch_task(self.task)

        harness.cancel_task("task")

        result = harness.collect_result("task")
        self.assertEqual(result.task_id, "task")
        self.assertEqual(result.status, "cancelled")

    def test_collect_rejects_unknown_task(self) -> None:
        with self.assertRaises(KeyError):
            CodexPromptHarness().collect_result("unknown")
