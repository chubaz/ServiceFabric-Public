import unittest
from pydantic import ValidationError
from servicefabric_contracts import ToolsetDefinition
class ToolsetTests(unittest.TestCase):
 def test_members_are_deterministic_and_unique(self):
  base={"apiVersion":"servicefabric.ai/v1alpha1","kind":"ToolsetDefinition","metadata":{"id":"core-tools","name":"Core","description":"Core tools","owner_ref":{"kind":"team","id":"platform"}},"spec":{"toolset_id":"core-tools","description":"Core tools","members":[{"tool_id":"math.calculate","revision_ref":"1.0.0"}]}}
  self.assertEqual(ToolsetDefinition.model_validate(base).spec.members[0].tool_id,"math.calculate")
  base["spec"]["members"]*=2
  with self.assertRaises(ValidationError):ToolsetDefinition.model_validate(base)
