class ServiceFabricTool:
 def __init__(self,client,tool_id,request_factory):self.client=client;self.tool_id=tool_id;self.name=tool_id.replace(".","_");self.request_factory=request_factory
 def invoke(self,arguments):
  result=self.client.invoke(self.request_factory(self.tool_id,arguments))
  if result.status=="error":raise RuntimeError(result.error.message)
  return {"data":result.data,"warnings":[w.model_dump(mode="json") for w in result.warnings],"evidence":[e.model_dump(mode="json") for e in result.evidence],"effect_receipts":[e.model_dump(mode="json") for e in result.effect_receipts]}
class ServiceFabricToolset:
 def __init__(self,client,toolset_id,members,request_factory):self.client=client;self.toolset_id=toolset_id;self.members=tuple(sorted(members));self.request_factory=request_factory
 def load_tools(self):return [ServiceFabricTool(self.client,x,self.request_factory) for x in self.members]
