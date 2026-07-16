import unittest
from servicefabric_agent_harness import CodexPromptHarness
from servicefabric_agentic_contracts import AgentTask
class HarnessTests(unittest.TestCase):
 def test_render_has_boundaries(self):
  self.assertIn("Allowed paths: x",CodexPromptHarness().render_task(AgentTask(task_id="task",role="role",objective="do",allowed_paths=("x",))))
