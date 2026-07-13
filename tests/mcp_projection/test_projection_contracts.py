import unittest
from datetime import datetime,timedelta,timezone
from pydantic import ValidationError
from servicefabric_mcp_projection import McpCallRequest,McpEnvelope,McpSessionContext,ProjectedMcpTool
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
CALLER={"subject_ref":"user-alice","principal_type":"human","tenant_ref":"tenant-demo","issuer":"servicefabric-identity","scopes":["math-calculate"],"authentication_strength":"multi_factor"}
class ProjectionContractTests(unittest.TestCase):
 def test_strict_deterministic_models(self):
  tool=ProjectedMcpTool(name="math-calculate",canonical_tool_id="math.calculate",revision_ref="1.0.0",title="Calculate",description="Bounded calculator.",input_schema={"type":"object"})
  self.assertEqual(tool.model_dump_json(),tool.model_dump_json())
  with self.assertRaises(ValidationError):ProjectedMcpTool.model_validate({**tool.model_dump(),"unknown":True})
 def test_call_excludes_raw_keys_and_timestamps_are_safe(self):
  with self.assertRaises(ValidationError):McpCallRequest(request_id="request-1",tool_name="math-calculate",correlation_id="corr-1",arguments={"api_key":"secret"})
  with self.assertRaises(ValidationError):McpCallRequest(request_id="request-1",tool_name="math-calculate",correlation_id="corr-1",deadline_at=datetime(2030,1,1))
 def test_session_and_envelope_are_bounded(self):
  session=McpSessionContext(session_id="session-1",caller=CALLER,adapter_ref="trusted-mcp-adapter",negotiated_capabilities={},created_at=NOW,expires_at=NOW+timedelta(minutes=5))
  self.assertEqual(session.caller.subject_ref,"user-alice")
  with self.assertRaises(ValidationError):McpEnvelope(message_type="tools_call",payload={"authorization":"secret"})
if __name__=="__main__":unittest.main()
