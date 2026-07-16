import tempfile
import unittest
from servicefabric_agentic_contracts import AgentTaskResult, ApplicationIntent
from servicefabric_agentic_planner import compile_plan
from servicefabric_agentic_orchestrator import ready_tasks
from servicefabric_agentic_run_store import FileRunStore
class FrameworkJourneyTests(unittest.TestCase):
 def test_intent_to_durable_handoff(self):
  with tempfile.TemporaryDirectory() as root:
   plan=compile_plan(ApplicationIntent(intent_id="journey",mode="create",objective="create app")); self.assertEqual(len(ready_tasks(plan)),1)
   store=FileRunStore(root); store.save_plan(plan); store.record_result(plan.run_id,AgentTaskResult(task_id=plan.tasks[0].task_id,status="success")); self.assertEqual(store.handoff(plan.run_id).status,"success")
