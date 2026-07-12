from servicefabric_contracts import ApplicationBuildRequest
class ServiceFabricClient:
 def __init__(self,runtime,caller_context=None):self.runtime=runtime;self.caller_context=caller_context
 def invoke(self,request):return self.runtime.invoke(request.model_dump(mode="json",by_alias=True))
 def list_applications(self):return self.runtime.list_applications()
 def describe_application(self,application_id):return self.runtime.describe_application(application_id)
 def build_application(self,application_id,revision):
  if self.caller_context is None:raise ValueError("verified caller context is required")
  request_id=f"request.{application_id}.{revision.replace('.','-')}"
  request=ApplicationBuildRequest.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ApplicationBuildRequest","metadata":{"id":request_id,"name":"Application build","description":"Bounded application build request","owner_ref":{"kind":"service","id":"servicefabric-client"}},"spec":{"request_id":request_id,"application_id":application_id,"revision":revision,"caller_context":self.caller_context}})
  return self.runtime.build_application(request)
 def get_artifact_manifest(self,artifact_digest):return self.runtime.get_artifact_manifest(artifact_digest)
 def verify_artifact(self,artifact_digest):return self.runtime.verify_artifact(artifact_digest)
 def open_artifact_file(self,artifact_digest,path):return self.runtime.open_artifact_file(artifact_digest,path)
