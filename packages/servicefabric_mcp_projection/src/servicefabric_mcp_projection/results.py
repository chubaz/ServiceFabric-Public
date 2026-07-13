"""Safe deterministic projection of canonical result and error envelopes."""
from servicefabric_contracts.errors import ToolError
from servicefabric_contracts.results import ToolResult
from .models import McpCallResponse,McpProtocolError
ERRORS={"SF-VALID":"validation","SF-AUTH":"authorization_denied","SF-APPROVAL":"approval_required","SF-POLICY":"authorization_denied","SF-BUDGET":"timeout","SF-DEPEND":"dependency_unavailable","SF-EXEC":"execution_failed","SF-EFFECT":"effect_uncertain","SF-RUNTIME":"internal"}
def project_error(error:ToolError|None)->McpProtocolError:
 if error is None:return McpProtocolError(code="internal",message="Internal projection failure.")
 code=next((value for prefix,value in ERRORS.items() if error.code.startswith(prefix)),"internal")
 if error.code.startswith("SF-APPROVAL") and "INVALID" in error.code:code="approval_invalid"
 return McpProtocolError(code=code,message=error.message[:512],retryable=error.retryable)
def project_result(request_id:str,result:ToolResult,*,structured:bool,maximum_text_bytes:int=4096)->McpCallResponse:
 if result.status=="error":return McpCallResponse(request_id=request_id,error=project_error(result.error))
 if structured:return McpCallResponse(request_id=request_id,structured_content=result.data)
 text=str(result.data)[:maximum_text_bytes]
 return McpCallResponse(request_id=request_id,content=(text,))
