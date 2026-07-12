import unittest
from scripts.agent.validate_workplans import validate
from scripts.agent.common import safe_path
class WorkplanTests(unittest.TestCase):
 def test_configuration_validates(self): self.assertTrue(validate())
 def test_path_traversal_rejected(self):
  with self.assertRaises(ValueError): safe_path("../../outside")
