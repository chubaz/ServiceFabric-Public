from dataclasses import dataclass
import json,re
@dataclass(frozen=True)
class AllowedTool:
 remote_name:str;canonical_tool_id:str;expected_schema_digest:str
@dataclass(frozen=True)
class ServerConfiguration:
 server_id:str;transport:str;endpoint_ref:str;credential_binding_ref:str|None;allowed_tools:tuple[AllowedTool,...]
 @classmethod
 def load(cls,path):
  data=json.loads(path.read_text(encoding="utf-8")); text=json.dumps(data).lower()
  if re.search(r'"(?:token|password|secret|api_key|authorization|cookie)"',text):raise ValueError("literal credentials are forbidden")
  if data["transport"]!="streamable_http":raise ValueError("unsupported transport")
  tools=tuple(AllowedTool(**item) for item in data["allowed_tools"])
  if len({x.canonical_tool_id for x in tools})!=len(tools):raise ValueError("duplicate allowed tool")
  return cls(data["server_id"],data["transport"],data["endpoint_ref"],data.get("credential_binding_ref"),tools)
 def selected(self,tool_id):
  match=[x for x in self.allowed_tools if x.canonical_tool_id==tool_id]
  if len(match)!=1:raise KeyError("remote tool is not allowlisted")
  return match[0]
