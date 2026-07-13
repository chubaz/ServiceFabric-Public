"""Deterministic in-process MCP exchange and transcript replay harness."""
from dataclasses import dataclass
import json
from servicefabric_mcp_projection import InProcessTransport
class TranscriptError(ValueError):pass
@dataclass(frozen=True,slots=True)
class GoldenTranscript:
 exchanges:tuple[tuple[dict,dict],...]
 def canonical(self):return json.dumps([[request,response] for request,response in self.exchanges],sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n"
 @classmethod
 def parse(cls,value:str):
  payload=json.loads(value)
  if not isinstance(payload,list) or len(payload)>128:raise TranscriptError("invalid transcript")
  return cls(tuple((item[0],item[1]) for item in payload))
class McpHarness:
 def __init__(self,handler):self._transport=InProcessTransport(handler)
 def exchange(self,request:dict)->dict:return self._transport.exchange(request)
 def replay(self,transcript:GoldenTranscript)->None:
  for request,expected in transcript.exchanges:
   if self.exchange(request)!=expected:raise TranscriptError("transcript response mismatch")
