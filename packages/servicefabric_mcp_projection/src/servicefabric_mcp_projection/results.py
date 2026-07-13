"""Safe deterministic projection of canonical result and error envelopes."""
import json
from servicefabric_contracts.errors import ToolError
from servicefabric_contracts.results import ToolResult
from servicefabric_contracts.invocation import ToolInvocationAcceptance
from .models import McpCallResponse,McpProtocolError
ERRORS={"SF-VALID":"validation","SF-AUTH":"authorization_denied","SF-APPROVAL":"approval_required","SF-POLICY":"authorization_denied","SF-BUDGET":"timeout","SF-DEPEND":"dependency_unavailable","SF-EXEC":"execution_failed","SF-EFFECT":"effect_uncertain","SF-RUNTIME":"internal"}
def project_error(error:ToolError|None)->McpProtocolError:
 if error is None:return McpProtocolError(code="internal",message="Internal projection failure.")
 code=next((value for prefix,value in ERRORS.items() if error.code.startswith(prefix)),"internal")
 if error.code.startswith("SF-APPROVAL") and "INVALID" in error.code:code="approval_invalid"
 if code=="internal":return McpProtocolError(code=code,message="Internal execution failure.",retryable=False)
 return McpProtocolError(code=code,message=error.message[:512],retryable=error.retryable)
def project_result(request_id:str,result:ToolResult,*,structured:bool,maximum_text_bytes:int=4096)->McpCallResponse:
 if result.status=="error":return McpCallResponse(request_id=request_id,error=project_error(result.error))
 if structured:return McpCallResponse(request_id=request_id,structured_content=result.data)
 if maximum_text_bytes<1 or maximum_text_bytes>4096:raise ValueError("invalid text response limit")
 text=(result.data if isinstance(result.data,str) else json.dumps(result.data,sort_keys=True,separators=(",",":"),ensure_ascii=True))[:maximum_text_bytes]
 return McpCallResponse(request_id=request_id,content=(text,))
def project_acceptance(acceptance:ToolInvocationAcceptance)->McpCallResponse:
 return McpCallResponse(request_id=acceptance.request_id,operation_ref=acceptance.operation_ref,content=("Operation accepted.",))
