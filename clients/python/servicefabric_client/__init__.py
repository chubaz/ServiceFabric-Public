class ServiceFabricClient:
 def __init__(self,runtime):self.runtime=runtime
 def invoke(self,request):return self.runtime.invoke(request.model_dump(mode="json",by_alias=True))
