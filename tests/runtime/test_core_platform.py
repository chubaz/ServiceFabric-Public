import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/"packages/servicefabric_contracts/src"),str(ROOT/"packages/servicefabric_runtime")]
from servicefabric_contracts import ToolInvocationRequest
from servicefabric_runtime import FilePortfolio,InvocationKernel
class CorePlatformTests(unittest.TestCase):
 def request(self): return ToolInvocationRequest.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ToolInvocationRequest","metadata":{"id":"request-1","name":"Calculation","description":"Calculate","owner_ref":{"kind":"service","id":"client"}},"spec":{"request_id":"request-1","target":{"target_kind":"revision","tool_id":"math.calculate","revision_ref":"1.0.0"},"arguments":{"expression":"2+3*4"},"caller_context":{"subject_ref":"client","principal_type":"service","issuer":"servicefabric","audiences":[],"scopes":[],"authentication_strength":"workload"},"protocol_context":{"protocol":"internal","adapter_ref":"python-client"},"budget":{}}})
 def test_vertical_slice(self):
  p=FilePortfolio(ROOT/"packages/servicefabric_runtime/portfolios");self.assertEqual(InvocationKernel(p).invoke(self.request()).data["value"],14)
 def test_path_and_expression_are_bounded(self):
  p=FilePortfolio(ROOT/"packages/servicefabric_runtime/portfolios")
  with self.assertRaises(ValueError):p.load("../escape")
