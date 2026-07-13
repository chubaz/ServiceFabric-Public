import unittest
from datetime import datetime,timezone
from servicefabric_contracts.caller import CallerContext
from servicefabric_contracts.operations import ServiceFabricOperation
from servicefabric_mcp_gateway import McpGatewayService
from servicefabric_mcp_projection import DiscoveryService,McpCancellationRequest,McpClientCapabilities,SessionManager,TrustedMcpTransportContext
from servicefabric_client.mcp import McpGatewayClient
from servicefabric_client.mcp_cli import execute
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def operation():return ServiceFabricOperation.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ServiceFabricOperation","metadata":{"id":"operation-1","name":"Operation","description":"Fixture.","owner_ref":{"kind":"service","id":"controller"}},"spec":{"operation_id":"operation-1","request_ref":"request-1","invocation_ref":"invocation-1","tool_id":"math.calculate","revision_ref":"1.0.0","state":"running","progress":50,"created_at":NOW,"updated_at":NOW,"cancellation":{"cancellable":True,"cancellation_state":"not_requested"}}})
class Operations:
 def __init__(self):self.cancelled=[]
 def get_operation(self,operation_ref):return operation(),3
 def request_cancellation(self,*args,**kwargs):self.cancelled.append((args,kwargs));return operation()
class GatewayOperationsTests(unittest.TestCase):
 def test_task_progress_and_cancellation_delegate_to_canonical_operations(self):
  operations=Operations();gateway=McpGatewayService(sessions=SessionManager(),discovery=DiscoveryService(()),tools=(),governed_invocations=object(),operations=operations)
  gateway.initialize(session_id="session-1",trusted_context=TrustedMcpTransportContext(caller=CallerContext(subject_ref="user-alice",principal_type="human",tenant_ref="tenant-demo",issuer="identity",authentication_strength="multi_factor"),adapter_ref="trusted-mcp-adapter"),capabilities=McpClientCapabilities(durable_operations=True,progress=True,cancellation=True),now=NOW)
  task=gateway.task(session_id="session-1",operation_ref="operation-1",now=NOW);self.assertEqual((task.task_id,task.operation_ref),("operation-1","operation-1"))
  progress=gateway.progress(session_id="session-1",request_id="request-1",operation_ref="operation-1",sequence=1,message="Canonical progress.",now=NOW);self.assertEqual(progress.progress,50)
  gateway.cancel(session_id="session-1",request=McpCancellationRequest(request_id="request-1",operation_ref="operation-1",reason="User cancelled."),expected_version=3,now=NOW);self.assertEqual(operations.cancelled[0][0][0],"operation-1")
  client=McpGatewayClient(gateway);self.assertEqual(__import__("json").loads(execute(client,["task","session-1","operation-1"],now=NOW))["task_id"],"operation-1")
