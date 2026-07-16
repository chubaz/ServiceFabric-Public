import json
import tempfile
import threading
import unittest
from pathlib import Path

from servicefabric_agentic_contracts import (
    AgentRunPlan,
    AgentTask,
    AgentTaskResult,
    ApplicationIntent,
)
from servicefabric_agentic_run_store import FileRunStore


def make_plan(*task_ids: str) -> AgentRunPlan:
    intent = ApplicationIntent(intent_id="intent", mode="create", objective="build")
    tasks = tuple(
        AgentTask(task_id=task_id, role="implementation", objective=task_id)
        for task_id in task_ids
    )
    return AgentRunPlan(
        run_id="run-intent",
        intent=intent,
        tasks=tasks,
        maximum_parallel_tasks=len(tasks),
    )


class StoreTests(unittest.TestCase):
    def test_resume_records_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileRunStore(root)
            plan = make_plan("task-one")

            store.save_plan(plan)
            store.record_result(
                plan.run_id,
                AgentTaskResult(task_id="task-one", status="success"),
            )

            resumed = FileRunStore(root)
            self.assertEqual(resumed.handoff(plan.run_id).status, "success")
            self.assertFalse(Path(root, "run-intent.tmp").exists())

    def test_parallel_results_are_not_lost(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileRunStore(root)
            plan = make_plan("task-one", "task-two")
            store.save_plan(plan)
            barrier = threading.Barrier(2)

            def record(task_id: str) -> None:
                barrier.wait()
                store.record_result(
                    plan.run_id,
                    AgentTaskResult(task_id=task_id, status="success"),
                )

            threads = [
                threading.Thread(target=record, args=(task.task_id,))
                for task in plan.tasks
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            handoff = store.handoff(plan.run_id)
            self.assertEqual(handoff.status, "success")
            self.assertEqual(
                tuple(result.task_id for result in handoff.task_results),
                ("task-one", "task-two"),
            )

    def test_handoff_tracks_pending_progress_and_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileRunStore(root)
            plan = make_plan("task-one", "task-two")
            store.save_plan(plan)
            self.assertEqual(store.handoff(plan.run_id).status, "pending")

            store.record_result(
                plan.run_id,
                AgentTaskResult(task_id="task-one", status="success"),
            )
            self.assertEqual(store.handoff(plan.run_id).status, "running")

            store.record_result(
                plan.run_id,
                AgentTaskResult(
                    task_id="task-two",
                    status="blocked",
                    blockers=("needs approval",),
                ),
            )
            handoff = store.handoff(plan.run_id)
            self.assertEqual(handoff.status, "blocked")
            self.assertEqual(handoff.unresolved_blockers, ("needs approval",))

    def test_handoff_distinguishes_cancelled_from_pending(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileRunStore(root)
            plan = make_plan("task-one", "task-two")
            store.save_plan(plan)
            store.record_result(
                plan.run_id,
                AgentTaskResult(task_id="task-one", status="cancelled"),
            )
            store.record_result(
                plan.run_id,
                AgentTaskResult(task_id="task-two", status="pending"),
            )
            self.assertEqual(store.handoff(plan.run_id).status, "running")

            store.record_result(
                plan.run_id,
                AgentTaskResult(task_id="task-two", status="success"),
            )
            self.assertEqual(store.handoff(plan.run_id).status, "cancelled")

    def test_plan_save_is_idempotent_but_cannot_replace_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileRunStore(root)
            plan = make_plan("task-one")
            store.save_plan(plan)
            store.record_result(
                plan.run_id,
                AgentTaskResult(task_id="task-one", status="success"),
            )
            store.save_plan(plan)
            self.assertEqual(store.handoff(plan.run_id).status, "success")

            replacement = plan.model_copy(
                update={
                    "tasks": (
                        AgentTask(
                            task_id="task-two",
                            role="implementation",
                            objective="replacement",
                        ),
                    )
                }
            )
            with self.assertRaisesRegex(ValueError, "different plan"):
                store.save_plan(replacement)

    def test_rejects_unknown_tasks_and_unsafe_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileRunStore(root)
            store.save_plan(make_plan("task-one"))
            with self.assertRaisesRegex(ValueError, "does not belong"):
                store.record_result(
                    "run-intent",
                    AgentTaskResult(task_id="task-two", status="success"),
                )
            with self.assertRaisesRegex(ValueError, "invalid run_id"):
                store.load("../outside")

    def test_rejects_corrupt_or_mismatched_state(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            store = FileRunStore(root)
            plan = make_plan("task-one")
            store.save_plan(plan)
            path = Path(root, "run-intent.json")
            state = json.loads(path.read_text(encoding="utf-8"))
            state["results"]["task-one"] = AgentTaskResult(
                task_id="task-two", status="success"
            ).model_dump(mode="json")
            path.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "invalid result task"):
                store.load(plan.run_id)


if __name__ == "__main__":
    unittest.main()
