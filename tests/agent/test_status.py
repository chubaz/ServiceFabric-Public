import unittest
from scripts.agent.common import read_json
class StatusTests(unittest.TestCase):
 def test_current_status(self): self.assertEqual(read_json("docs/workplans/status.json")["current_milestone"],"v1-00")
