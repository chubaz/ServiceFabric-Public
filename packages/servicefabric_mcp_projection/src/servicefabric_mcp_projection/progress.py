"""Progress and cancellation projections delegate to canonical operation services."""
from .models import McpCancellationRequest,McpProgressNotification
class ProgressProjector:
 def project(self,*,request_id:str,operation_ref:str|None,sequence:int,progress:int,message:str,client_supports_progress:bool):
  if not client_supports_progress:return None
  return McpProgressNotification(request_id=request_id,operation_ref=operation_ref,sequence=sequence,progress=progress,message=message)
class CancellationProjector:
 def __init__(self,operations_service):self._operations_service=operations_service
 def cancel(self,request:McpCancellationRequest,*,expected_version:int,now):
  return self._operations_service.request_cancellation(request.operation_ref,expected_version=expected_version,now=now,reason=request.reason)
