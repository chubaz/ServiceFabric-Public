"""Deterministic in-process MCP exchange and transcript replay harness."""
from dataclasses import dataclass
import json
from servicefabric_mcp_projection import InProcessTransport
class TranscriptError(ValueError):pass
@dataclass(frozen=True,slots=True)
class GoldenTranscript:
 exchanges:tuple[tuple[dict,dict],...]
 def canonical(self):
  if len(self.exchanges)>128:raise TranscriptError("transcript exchange limit exceeded")
  value=json.dumps([[request,response] for request,response in self.exchanges],sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n"
  if len(value.encode())>65536:raise TranscriptError("transcript exceeds byte limit")
  return value
 @classmethod
 def parse(cls,value:str):
  payload=json.loads(value)
  if not isinstance(payload,list) or len(payload)>128:raise TranscriptError("invalid transcript")
  exchanges=[]
  for item in payload:
   if not isinstance(item,list) or len(item)!=2 or not isinstance(item[0],dict) or not isinstance(item[1],dict):raise TranscriptError("transcript exchanges must be request/response objects")
   exchanges.append((item[0],item[1]))
  return cls(tuple(exchanges))
@dataclass(frozen=True,slots=True)
class HarnessFixtures:
 caller:dict
 now:str="2030-01-01T00:00:00Z"
 session_id:str="session-fixture"
 request_id:str="request-fixture"
 inventory:tuple[dict,...]=()
class McpHarness:
 def __init__(self,handler):self._transport=InProcessTransport(handler)
 def exchange(self,request:dict)->dict:return self._transport.exchange(request)
 def replay(self,transcript:GoldenTranscript)->None:
  for request,expected in transcript.exchanges:
   if self.exchange(request)!=expected:raise TranscriptError("transcript response mismatch")
