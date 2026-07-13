"""MCP call to canonical invocation translation; no execution occurs here."""
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.invocation import InvocationIdempotency,RevisionInvocationTarget,ToolInvocationRequest
from servicefabric_contracts.metadata import OwnerReference,ResourceMetadata
from servicefabric_contracts.protocol import ProtocolContext
from .models import McpCallRequest,McpSessionContext,ProjectedMcpTool
class CallTranslationError(ValueError):pass
class CallTranslator:
 def __init__(self,tools:tuple[ProjectedMcpTool,...]):
  names=tuple(tool.name for tool in tools)
  if len(set(names))!=len(names):raise ValueError("projected MCP tool names must be unique")
  self._tools={tool.name:tool for tool in tools}
 def translate(self,call:McpCallRequest,session:McpSessionContext)->ToolInvocationRequest:
  tool=self._tools.get(call.tool_name)
  if tool is None:raise CallTranslationError("projected tool was not found")
  if session.caller.principal_type=="anonymous":raise CallTranslationError("trusted authenticated caller is required")
  idempotency=InvocationIdempotency(key_digest=call.idempotency_digest,scope="caller",replay_policy="return_previous",caller_intent="mcp-call") if call.idempotency_digest else None
  return ToolInvocationRequest(apiVersion="servicefabric.ai/v1alpha1",kind="ToolInvocationRequest",metadata=ResourceMetadata(id=call.request_id,name="MCP projected invocation",description="Canonical request translated from a bounded MCP call.",owner_ref=OwnerReference(kind="service",id="mcp-gateway")),spec={"request_id":call.request_id,"target":RevisionInvocationTarget(target_kind="revision",tool_id=tool.canonical_tool_id,revision_ref=tool.revision_ref),"arguments":call.arguments,"caller_context":session.caller,"protocol_context":ProtocolContext(protocol="mcp",adapter_ref=session.adapter_ref,session_ref=session.session_id,remote_request_ref=call.request_id,projection_metadata={"correlation":call.correlation_id}),"budget":ExecutionBudget(deadline=call.deadline_at),"idempotency":idempotency,"approval_refs":(call.approval_binding_ref,) if call.approval_binding_ref else (),"requested_response_mode":"either"})
