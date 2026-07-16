import unittest
from servicefabric_agentic_contracts import ApplicationIntent
from servicefabric_agentic_planner import compile_plan
class PlannerTests(unittest.TestCase):
 def test_plan_is_deterministic(self):
  plan=compile_plan(ApplicationIntent(intent_id="intent",mode="create",objective="build"))
  self.assertEqual(plan.run_id,"run-intent")
