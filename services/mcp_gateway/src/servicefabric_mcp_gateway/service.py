"""Inbound MCP gateway facade delegating only to canonical service boundaries."""
from servicefabric_contracts.invocation import ToolInvocationAcceptance
from servicefabric_mcp_projection import CallTranslator,CancellationProjector,McpCallRequest,McpCancellationRequest,SessionManager,project_acceptance,project_result,project_task
class McpGatewayService:
 def __init__(self,*,sessions:SessionManager,discovery,tools,governed_invocations,operations):self._sessions=sessions;self._discovery=discovery;self._translator=CallTranslator(tools);self._invocations=governed_invocations;self._operations=operations
 def initialize(self,*,session_id,trusted_context,capabilities,now):return self._sessions.initialize(session_id=session_id,trusted_context=trusted_context,capabilities=capabilities,now=now)
 def list_tools(self,*,session_id,now,cursor=None,page_size=16):
  session=self._sessions.request(session_id,now=now);return self._discovery.list_tools(session.caller,cursor=cursor,page_size=page_size)
 def call(self,*,session_id,call:McpCallRequest,now):
  session=self._sessions.request(session_id,now=now);request=self._translator.translate(call,session);outcome=self._invocations.invoke(request,trusted_adapter_ref=session.adapter_ref,now=now)
  if isinstance(outcome,ToolInvocationAcceptance):return project_acceptance(outcome)
  return project_result(call.request_id,outcome,structured=session.negotiated_capabilities.structured_results)
 def task(self,*,session_id,operation_ref,now):
  session=self._sessions.request(session_id,now=now);operation=self._operation(operation_ref);return project_task(operation,client_supports_tasks=session.negotiated_capabilities.durable_operations)
 def progress(self,*,session_id,request_id,operation_ref,sequence,message,now):
  session=self._sessions.request(session_id,now=now);operation=self._operation(operation_ref)
  if not session.negotiated_capabilities.progress or operation.spec.progress is None:return None
  from servicefabric_mcp_projection import ProgressProjector
  return ProgressProjector().project(request_id=request_id,operation_ref=operation_ref,sequence=sequence,progress=operation.spec.progress,message=message,client_supports_progress=True)
 def cancel(self,*,session_id,request:McpCancellationRequest,expected_version,now):
  self._sessions.request(session_id,now=now);return CancellationProjector(self._operations).cancel(request,expected_version=expected_version,now=now)
 def _operation(self,operation_ref):
  value=self._operations.get_operation(operation_ref)
  return value[0] if isinstance(value,tuple) else value
