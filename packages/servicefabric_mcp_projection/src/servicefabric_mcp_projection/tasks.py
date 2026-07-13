"""Non-authoritative MCP views over canonical durable operations."""
from servicefabric_contracts.operations import ServiceFabricOperation
from .models import McpTaskView
from .results import project_error
def project_task(operation:ServiceFabricOperation,*,client_supports_tasks:bool):
 if not client_supports_tasks:return None
 return McpTaskView(task_id=operation.spec.operation_id,operation_ref=operation.spec.operation_id,state=operation.spec.state,progress=operation.spec.progress,cancellation_state=operation.spec.cancellation.cancellation_state,result_ref=operation.spec.result_ref,error=project_error(operation.spec.error) if operation.spec.error else None)
