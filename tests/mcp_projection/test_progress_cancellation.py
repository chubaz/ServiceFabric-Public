import unittest
from test_gateway_operations import GatewayOperationsTests
from datetime import datetime,timezone
from servicefabric_mcp_projection import CancellationProjector,McpCancellationRequest,ProgressProjector
class FakeOperations:
 def __init__(self):self.calls=[]
 def request_cancellation(self,*args,**kwargs):self.calls.append((args,kwargs));return "canonical-cancellation"
class ProgressCancellationTests(unittest.TestCase):
 def test_progress_only_projects_canonical_values_for_capable_clients(self):
  projector=ProgressProjector();self.assertIsNone(projector.project(request_id="request-1",operation_ref=None,sequence=1,progress=50,message="Halfway.",client_supports_progress=False));self.assertEqual(projector.project(request_id="request-1",operation_ref="operation-1",sequence=1,progress=50,message="Halfway.",client_supports_progress=True).progress,50)
 def test_cancellation_delegates_without_store_access(self):
  service=FakeOperations();value=CancellationProjector(service).cancel(McpCancellationRequest(request_id="request-1",operation_ref="operation-1",reason="User cancelled."),expected_version=2,now=datetime(2030,1,1,tzinfo=timezone.utc));self.assertEqual(value,"canonical-cancellation");self.assertEqual(service.calls[0][0][0],"operation-1")
if __name__=="__main__":unittest.main()
