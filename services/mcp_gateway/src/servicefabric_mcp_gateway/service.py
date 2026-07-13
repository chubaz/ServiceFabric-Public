"""Inbound MCP gateway facade delegating only to canonical service boundaries."""
from servicefabric_mcp_projection import CallTranslator,McpCallRequest,McpClientCapabilities,SessionManager,project_result
class McpGatewayService:
 def __init__(self,*,sessions:SessionManager,discovery,tools,canonical_runtime):self._sessions=sessions;self._discovery=discovery;self._translator=CallTranslator(tools);self._runtime=canonical_runtime
 def initialize(self,*,session_id,trusted_context,capabilities,now):return self._sessions.initialize(session_id=session_id,trusted_context=trusted_context,capabilities=capabilities,now=now)
 def list_tools(self,*,session_id,now,cursor=None,page_size=16):
  session=self._sessions.request(session_id,now=now);return self._discovery.list_tools(session.caller,cursor=cursor,page_size=page_size)
 def call(self,*,session_id,call:McpCallRequest,now):
  session=self._sessions.request(session_id,now=now);request=self._translator.translate(call,session);result=self._runtime.invoke(request.model_dump(mode="json",by_alias=True));return project_result(call.request_id,result,structured=session.negotiated_capabilities.structured_results)
