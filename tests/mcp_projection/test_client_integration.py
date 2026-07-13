import unittest
from datetime import datetime,timedelta,timezone
from servicefabric_client.mcp import McpGatewayClient
from servicefabric_client.mcp_cli import execute
from servicefabric_contracts.results import ToolResult
from servicefabric_contracts.caller import CallerContext
from servicefabric_mcp_gateway import McpGatewayService
from servicefabric_mcp_projection import DiscoveryService,McpCallRequest,McpClientCapabilities,ProjectedMcpTool,ProjectionCandidate,SessionManager,TrustedMcpTransportContext
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
class Runtime:
 def __init__(self):self.requests=[]
 def invoke(self,payload):
  self.requests.append(payload);return ToolResult(apiVersion="servicefabric.ai/v1alpha1",kind="ToolResult",status="success",invocation_id=payload["spec"]["request_id"],tool_id="math.calculate",revision_ref="1.0.0",started_at=NOW,completed_at=NOW,duration=timedelta(),data={"value":2})
def client():
 candidate=ProjectionCandidate("math.calculate","1.0.0","math-calculate","Calculate","Calculate.",{},True,True,("math-calculate",),structured_result=True);runtime=Runtime();tool=ProjectedMcpTool(name="math-calculate",canonical_tool_id="math.calculate",revision_ref="1.0.0",title="Calculate",description="Calculate.",input_schema={},structured_result=True);gateway=McpGatewayService(sessions=SessionManager(),discovery=DiscoveryService((candidate,)),tools=(tool,),canonical_runtime=runtime);return McpGatewayClient(gateway),runtime
def initialize(value):return value.initialize(session_id="session-1",trusted_context=TrustedMcpTransportContext(caller=CallerContext(subject_ref="user-alice",principal_type="human",tenant_ref="tenant-demo",issuer="identity",scopes=("math-calculate",),authentication_strength="multi_factor"),adapter_ref="trusted-mcp-adapter"),capabilities=McpClientCapabilities(structured_results=True),now=NOW)
class ClientIntegrationTests(unittest.TestCase):
 def test_gateway_initialization_does_not_accept_caller_fields(self):
  value,_=client()
  with self.assertRaises(TypeError):value.initialize(session_id="session-1",caller=CallerContext(subject_ref="forged",principal_type="human",tenant_ref="tenant-demo",issuer="identity",authentication_strength="multi_factor"),adapter_ref="trusted-mcp-adapter",capabilities=McpClientCapabilities(),now=NOW)
 def test_client_delegates_discovery_and_call(self):
  value,runtime=client();initialize(value);self.assertEqual(value.list_tools(session_id="session-1",now=NOW).tools[0].name,"math-calculate");response=value.call(session_id="session-1",now=NOW,call=McpCallRequest(request_id="request-1",tool_name="math-calculate",correlation_id="corr-1",arguments={"expression":"1+1"}));self.assertEqual(response.structured_content,{"value":2});self.assertEqual(runtime.requests[0]["spec"]["protocol_context"]["protocol"],"mcp")
 def test_cli_is_machine_readable(self):
  value,_=client();initialize(value);self.assertEqual(__import__("json").loads(execute(value,["list","session-1"],now=NOW))["tools"][0]["name"],"math-calculate")
if __name__=="__main__":unittest.main()
