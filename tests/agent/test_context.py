import unittest
from scripts.agent.context import context
class ContextTests(unittest.TestCase):
 def test_context_is_bounded(self):
  value=context("v1-00");self.assertGreater(len(value["files"]),0);self.assertLess(len(value["files"]),20)
