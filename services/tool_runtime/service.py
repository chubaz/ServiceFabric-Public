"""Internal in-process runtime boundary; transport adapters are deferred."""
from servicefabric_contracts import ToolInvocationRequest
class ToolRuntimeService:
 def __init__(self,kernel):self.kernel=kernel
 def invoke(self,payload):return self.kernel.invoke(ToolInvocationRequest.model_validate(payload))
