"""Strict local MCP profile DTOs; they never replace canonical resources."""
from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from servicefabric_contracts.caller import CallerContext
from servicefabric_contracts.common import Identifier, ToolIdentifier, has_secret_like_key, is_json_value

class ProjectionModel(BaseModel):
 model_config=ConfigDict(extra="forbid",validate_assignment=True,str_strip_whitespace=True)
class McpClientCapabilities(ProjectionModel):
 structured_results:bool=False
 progress:bool=False
 cancellation:bool=False
 durable_operations:bool=False
class McpServerCapabilities(ProjectionModel):
 structured_results:bool=True
 progress:bool=True
 cancellation:bool=True
 durable_operations:bool=True
 in_process_transport:bool=True
class McpSessionContext(ProjectionModel):
 session_id:Identifier
 caller:CallerContext
 adapter_ref:Identifier
 negotiated_capabilities:McpClientCapabilities
 created_at:datetime
 expires_at:datetime
 request_count:int=Field(default=0,ge=0,le=256)
 @field_validator("created_at","expires_at")
 @classmethod
 def aware(cls,value):
  if value.tzinfo is None or value.utcoffset() is None:raise ValueError("session timestamps must be timezone-aware")
  return value
 @model_validator(mode="after")
 def window(self):
  if self.expires_at<=self.created_at:raise ValueError("session expiry must follow creation")
  return self
class ProjectedMcpTool(ProjectionModel):
 name:Identifier
 canonical_tool_id:ToolIdentifier
 revision_ref:str=Field(min_length=1,max_length=160,pattern=r"^[a-z0-9][a-z0-9._:-]+$")
 title:str=Field(min_length=1,max_length=160)
 description:str=Field(min_length=1,max_length=2000)
 input_schema:dict[str,object]=Field(default_factory=dict,max_length=128)
 structured_result:bool=False
 progress:bool=False
 cancellation:bool=False
 durable_operations:bool=False
 annotations:tuple[tuple[Identifier,str],...]=Field(default_factory=tuple,max_length=16)
 @field_validator("input_schema")
 @classmethod
 def safe_schema(cls,value):
  if not is_json_value(value) or any(has_secret_like_key(str(key)) for key in value):raise ValueError("tool schema must be safe JSON")
  return value
 @field_validator("revision_ref")
 @classmethod
 def revision(cls,value):
  if value in {"latest","current","production"}:raise ValueError("projection requires immutable revision")
  return value
class McpToolPage(ProjectionModel):
 tools:tuple[ProjectedMcpTool,...]=Field(default_factory=tuple,max_length=64)
 next_cursor:Identifier|None=None
class McpCallRequest(ProjectionModel):
 request_id:Identifier
 tool_name:Identifier
 arguments:dict[str,object]=Field(default_factory=dict,max_length=128)
 correlation_id:Identifier
 deadline_at:datetime|None=None
 idempotency_digest:str|None=Field(default=None,pattern=r"^sha256:[a-f0-9]{64}$")
 @field_validator("arguments")
 @classmethod
 def json_args(cls,value):
  if not is_json_value(value) or any(has_secret_like_key(str(key)) or str(key).lower() in {"authorization","cookie"} for key in value):raise ValueError("arguments must be safe JSON")
  return value
 @field_validator("deadline_at")
 @classmethod
 def deadline(cls,value):
  if value is not None and (value.tzinfo is None or value.utcoffset() is None):raise ValueError("deadline must be timezone-aware")
  return value
class McpProtocolError(ProjectionModel):
 code:Literal["validation","not_found","revision_conflict","authorization_denied","approval_required","approval_invalid","idempotency_conflict","timeout","cancelled","dependency_unavailable","execution_failed","effect_uncertain","internal"]
 message:str=Field(min_length=1,max_length=512)
 retryable:bool=False
class McpCallResponse(ProjectionModel):
 request_id:Identifier
 content:tuple[str,...]=Field(default_factory=tuple,max_length=32)
 structured_content:object|None=None
 error:McpProtocolError|None=None
 operation_ref:Identifier|None=None
 @model_validator(mode="after")
 def result(self):
  if self.error is not None and (self.content or self.structured_content is not None):raise ValueError("error response cannot contain result content")
  return self
class McpProgressNotification(ProjectionModel):
 request_id:Identifier
 operation_ref:Identifier|None=None
 sequence:int=Field(ge=1,le=1024)
 progress:int=Field(ge=0,le=100)
 message:str=Field(min_length=1,max_length=512)
class McpCancellationRequest(ProjectionModel):
 request_id:Identifier
 operation_ref:Identifier
 reason:str=Field(min_length=1,max_length=512)
class McpTaskView(ProjectionModel):
 task_id:Identifier
 operation_ref:Identifier
 state:Literal["accepted","queued","running","waiting_for_approval","waiting_for_dependency","waiting_for_human","succeeded","partially_succeeded","failed","cancelled","timed_out"]
 progress:int|None=Field(default=None,ge=0,le=100)
 cancellation_state:Literal["not_requested","requested","acknowledged","completed","rejected"]
 result_ref:Identifier|None=None
 error:McpProtocolError|None=None
class McpEnvelope(ProjectionModel):
 protocol_version:Literal["2025-03-26"]="2025-03-26"
 message_type:Literal["initialize","tools_list","tools_call","progress","cancel","task"]
 session_id:Identifier|None=None
 payload:dict[str,object]=Field(default_factory=dict,max_length=128)
 @field_validator("payload")
 @classmethod
 def safe_payload(cls,value):
  if not is_json_value(value) or any(has_secret_like_key(str(key)) or str(key).lower() in {"authorization","cookie"} for key in value):raise ValueError("protocol payload must be safe JSON")
  return value
