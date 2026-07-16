import tempfile
import unittest
from servicefabric_agentic_contracts import ApplicationIntent, AgentTaskResult
from servicefabric_agentic_planner import compile_plan
from servicefabric_agentic_run_store import FileRunStore
class StoreTests(unittest.TestCase):
 def test_resume_records_atomically(self):
  with tempfile.TemporaryDirectory() as root:
   store=FileRunStore(root); plan=compile_plan(ApplicationIntent(intent_id="intent",mode="create",objective="build")); store.save_plan(plan); store.record_result(plan.run_id,AgentTaskResult(task_id=plan.tasks[0].task_id,status="success")); self.assertEqual(store.handoff(plan.run_id).status,"success")
