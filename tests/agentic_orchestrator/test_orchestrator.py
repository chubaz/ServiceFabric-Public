import unittest
from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, ApplicationIntent
from servicefabric_agentic_orchestrator import ready_tasks
class OrchestratorTests(unittest.TestCase):
 def test_parallel_limit_is_enforced(self):
  intent=ApplicationIntent(intent_id="intent",mode="create",objective="build"); tasks=(AgentTask(task_id="one",role="x",objective="x"),AgentTask(task_id="two",role="x",objective="x")); self.assertEqual(len(ready_tasks(AgentRunPlan(run_id="run",intent=intent,tasks=tasks,maximum_parallel_tasks=1))),1)
