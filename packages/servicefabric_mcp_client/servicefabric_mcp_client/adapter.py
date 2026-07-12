from .errors import SchemaDriftError
from .schema import schema_digest
class FederatedMcpAdapter:
 def __init__(self,configuration,transport):self.configuration=configuration;self.transport=transport
 def invoke(self,tool_id,arguments):
  selected=self.configuration.selected(tool_id); remote=self.transport.describe(selected.remote_name)
  if schema_digest(remote["inputSchema"])!=selected.expected_schema_digest:raise SchemaDriftError("approved remote schema digest changed")
  result=self.transport.call(selected.remote_name,arguments)
  return {"data":result.get("structuredContent"),"text":result.get("text",[]),"is_error":bool(result.get("isError"))}
