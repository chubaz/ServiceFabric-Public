"""Internal in-process runtime boundary; transport adapters are deferred."""
from servicefabric_contracts import ToolInvocationRequest
class ToolRuntimeService:
 def __init__(self,kernel,*,toolset="core-tools"):self.kernel=kernel;self.toolset=toolset
 def invoke(self,payload):return self.kernel.invoke(ToolInvocationRequest.model_validate(payload),toolset=self.toolset)
