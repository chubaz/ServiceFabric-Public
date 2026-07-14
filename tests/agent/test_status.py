import unittest
from scripts.agent.common import read_json
class StatusTests(unittest.TestCase):
 def test_current_status(self): self.assertEqual(read_json("docs/workplans/status.json")["current_milestone"],"ap-00-modular-framework-kits")
