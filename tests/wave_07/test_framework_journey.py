from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOTS = (
    "packages/servicefabric_contracts/src",
    "packages/servicefabric_agentic_contracts/src",
    "packages/servicefabric_agentic_context/src",
    "packages/servicefabric_agentic_planner/src",
    "packages/servicefabric_agentic_run_store/src",
    "packages/servicefabric_agent_tools/src",
    "packages/servicefabric_agentic_orchestrator/src",
    "packages/servicefabric_agent_harness/src",
)
for source_root in reversed(SOURCE_ROOTS):
    sys.path.insert(0, str(REPOSITORY_ROOT / source_root))


from servicefabric_agent_harness import CodexPromptHarness
from servicefabric_agent_tools import BoundedAgentTools
from servicefabric_agentic_context import build_context_pack
from servicefabric_agentic_contracts import (
    AgentRunPlan,
    AgentTask,
    AgentTaskResult,
    ApplicationIntent,
    VerificationEvidence,
)
from servicefabric_agentic_orchestrator import ready_tasks
from servicefabric_agentic_planner import compile_plan
from servicefabric_agentic_run_store import FileRunStore


class FrameworkJourneyTests(unittest.TestCase):
    def test_intent_to_durable_evidenced_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as repository, tempfile.TemporaryDirectory() as state:
            root = Path(repository)
            (root / "AGENTS.md").write_text("# Agent policy\n", encoding="utf-8")
            (root / "README.md").write_text("# Application\n", encoding="utf-8")

            context = build_context_pack(
                root,
                application_id="sample-app",
                capability_ids=("weather", "search", "weather"),
            )
            self.assertEqual(context.repository, str(root.resolve()))
            self.assertEqual(context.files, ("AGENTS.md", "README.md"))
            self.assertEqual(context.capability_ids, ("search", "weather"))

            intent = ApplicationIntent(
                intent_id="journey",
                mode="create",
                objective="Create an application",
                application_id="sample-app",
                requested_capabilities=context.capability_ids,
            )
            plan = compile_plan(intent, run_id="run-journey", maximum_parallel_tasks=1)
            self.assertEqual(ready_tasks(plan), plan.tasks)

            task = plan.tasks[0]
            harness = CodexPromptHarness()
            self.assertEqual(
                harness.prepare_task(task, root),
                {"task_id": task.task_id, "repository": str(root.resolve())},
            )
            prompt = harness.render_task(task)
            self.assertEqual(prompt, harness.render_task(task))
            self.assertIn("Objective: Create an application", prompt)
            self.assertEqual(harness.launch_task(task), "prepared:journey")

            tools = BoundedAgentTools(root)
            inspection = tools.invoke("workspace.inspect", {"path": "README.md"})
            self.assertEqual(inspection.status, "success")
            self.assertEqual(inspection.data["path"], str((root / "README.md").resolve()))

            evidence = VerificationEvidence(
                command="python3 -m unittest discover -s tests/wave_07 -v",
                exit_code=0,
                summary="Wave-7 evaluation passed",
            )
            result = AgentTaskResult(
                task_id=task.task_id,
                status="success",
                changed_paths=("application.py",),
                commit_sha="0123456789abcdef0123456789abcdef01234567",
                evidence=(evidence,),
            )
            store = FileRunStore(state)
            store.save_plan(plan)
            store.record_result(plan.run_id, result)

            reloaded = FileRunStore(state)
            handoff = reloaded.handoff(plan.run_id)
            self.assertEqual(handoff.status, "success")
            self.assertEqual(handoff.task_results, (result,))
            self.assertEqual(handoff.task_results[0].evidence, (evidence,))
            self.assertEqual(handoff.unresolved_blockers, ())

    def test_blocked_dependency_is_not_scheduled_and_is_handed_off(self) -> None:
        intent = ApplicationIntent(
            intent_id="blocked-journey",
            mode="modify",
            objective="Modify an application",
            application_id="sample-app",
        )
        prepare = AgentTask(task_id="prepare", role="planner", objective="Prepare inputs")
        implement = AgentTask(
            task_id="implement",
            role="implementation",
            objective="Implement change",
            dependencies=(prepare.task_id,),
        )
        plan = AgentRunPlan(
            run_id="run-blocked-journey",
            intent=intent,
            tasks=(prepare, implement),
            maximum_parallel_tasks=2,
        )
        blocked = AgentTaskResult(
            task_id=prepare.task_id,
            status="blocked",
            blockers=("contract change required",),
        )

        self.assertEqual(ready_tasks(plan), (prepare,))
        self.assertEqual(ready_tasks(plan, (blocked,)), ())

        with tempfile.TemporaryDirectory() as state:
            store = FileRunStore(state)
            store.save_plan(plan)
            store.record_result(plan.run_id, blocked)
            handoff = store.handoff(plan.run_id)

        self.assertEqual(handoff.status, "blocked")
        self.assertEqual(handoff.unresolved_blockers, ("contract change required",))

    def test_tools_reject_repository_escape_and_unknown_operations(self) -> None:
        with tempfile.TemporaryDirectory() as repository:
            tools = BoundedAgentTools(repository)

            escaped = tools.invoke("workspace.inspect", {"path": "../outside"})
            unknown = tools.invoke("shell.execute", {"command": "true"})

        self.assertEqual(escaped.status, "blocked")
        self.assertEqual(escaped.summary, "path escapes repository")
        self.assertEqual(unknown.status, "blocked")
        self.assertEqual(unknown.summary, "tool is not allowlisted")


if __name__ == "__main__":
    unittest.main()
