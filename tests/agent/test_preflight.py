import unittest
from scripts.agent.preflight import inspect
class PreflightTests(unittest.TestCase):
 def test_ci_preflight(self): self.assertTrue(inspect("e0-00","ci")["ok"])
 def test_unknown_milestone(self):
  with self.assertRaises(KeyError): inspect("unknown","ci")
