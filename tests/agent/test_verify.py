import unittest
from scripts.agent.verify import verify
class VerifyTests(unittest.TestCase):
 def test_committed_commands_only(self): self.assertTrue(verify("v1-00","readiness")["ok"])
