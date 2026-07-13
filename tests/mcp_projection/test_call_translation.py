import unittest
from datetime import datetime,timedelta,timezone
from servicefabric_mcp_projection import CallTranslationError,CallTranslator,McpCallRequest,McpSessionContext,ProjectedMcpTool
NOW=datetime(2030,1,1,tzinfo=timezone.utc);D="sha256:"+"1"*64
def session():return McpSessionContext(session_id="session-1",caller={"subject_ref":"user-alice","principal_type":"human","tenant_ref":"tenant-demo","issuer":"identity","scopes":["math-calculate"],"authentication_strength":"multi_factor"},adapter_ref="trusted-mcp-adapter",negotiated_capabilities={},created_at=NOW,expires_at=NOW+timedelta(minutes=5))
def tool():return ProjectedMcpTool(name="math-calculate",canonical_tool_id="math.calculate",revision_ref="1.0.0",title="Calculate",description="Calculate.",input_schema={})
class CallTranslationTests(unittest.TestCase):
 def test_translation_preserves_trusted_caller_revision_and_idempotency(self):
  request=CallTranslator((tool(),)).translate(McpCallRequest(request_id="request-1",tool_name="math-calculate",correlation_id="correlation-1",arguments={"expression":"1+1"},idempotency_digest=D),session())
  self.assertEqual(request.spec.target.revision_ref,"1.0.0");self.assertEqual(request.spec.caller_context.subject_ref,"user-alice");self.assertEqual(request.spec.protocol_context.protocol,"mcp");self.assertEqual(request.spec.idempotency.key_digest,D)
 def test_unknown_tool_and_anonymous_session_are_rejected(self):
  with self.assertRaises(CallTranslationError):CallTranslator((tool(),)).translate(McpCallRequest(request_id="request-1",tool_name="unknown",correlation_id="corr-1"),session())
  value=session().model_copy(update={"caller":session().caller.model_copy(update={"principal_type":"anonymous","authentication_strength":"none","scopes":()})})
  with self.assertRaises(CallTranslationError):CallTranslator((tool(),)).translate(McpCallRequest(request_id="request-1",tool_name="math-calculate",correlation_id="corr-1"),value)
 def test_duplicate_projected_names_are_rejected(self):
  with self.assertRaises(ValueError):CallTranslator((tool(),tool()))
if __name__=="__main__":unittest.main()
