"""Bounded non-authoritative MCP session negotiation."""
from datetime import datetime,timedelta
from servicefabric_contracts.caller import CallerContext
from .models import McpClientCapabilities,McpServerCapabilities,McpSessionContext
class SessionError(ValueError):pass
class SessionManager:
 def __init__(self,*,maximum_sessions:int=32,maximum_requests:int=256,lifetime:timedelta=timedelta(minutes=30)):self._maximum_sessions=maximum_sessions;self._maximum_requests=maximum_requests;self._lifetime=lifetime;self._sessions={}
 def initialize(self,*,session_id:str,caller:CallerContext,adapter_ref:str,capabilities:McpClientCapabilities,now:datetime)->tuple[McpSessionContext,McpServerCapabilities]:
  if not adapter_ref.startswith("trusted-") or caller.principal_type=="anonymous":raise SessionError("trusted authenticated transport context is required")
  if session_id in self._sessions:raise SessionError("session is already initialized")
  if len(self._sessions)>=self._maximum_sessions:raise SessionError("session limit reached")
  session=McpSessionContext(session_id=session_id,caller=caller,adapter_ref=adapter_ref,negotiated_capabilities=capabilities,created_at=now,expires_at=now+self._lifetime)
  self._sessions[session_id]=session;return session,McpServerCapabilities()
 def request(self,session_id:str,*,now:datetime)->McpSessionContext:
  session=self._sessions.get(session_id)
  if session is None or now>=session.expires_at:raise SessionError("session is unavailable")
  if session.request_count>=self._maximum_requests:raise SessionError("session request limit reached")
  updated=session.model_copy(update={"request_count":session.request_count+1});self._sessions[session_id]=updated;return updated
 def discard(self,session_id:str)->None:self._sessions.pop(session_id,None)
