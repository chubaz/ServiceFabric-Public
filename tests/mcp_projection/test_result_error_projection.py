import unittest
from datetime import datetime,timedelta,timezone
from servicefabric_contracts.errors import ToolError
from servicefabric_contracts.results import ToolResult
from servicefabric_mcp_projection import project_error,project_result
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def result(status="success",error=None,data={"value":2}):return ToolResult(apiVersion="servicefabric.ai/v1alpha1",kind="ToolResult",status=status,invocation_id="invocation-1",tool_id="math.calculate",revision_ref="1.0.0",started_at=NOW,completed_at=NOW+timedelta(seconds=1),duration=timedelta(seconds=1),data=data,error=error)
class ResultErrorTests(unittest.TestCase):
 def test_structured_and_bounded_text_projection(self):
  self.assertEqual(project_result("request-1",result(),structured=True).structured_content,{"value":2});self.assertEqual(project_result("request-1",result(data="x"*100),structured=False,maximum_text_bytes=8).content,("x"*8,))
 def test_safe_error_mapping_redacts_details(self):
  error=ToolError(code="SF-APPROVAL-INVALID",category="approval",message="Approval is invalid.",details={})
  self.assertEqual(project_error(error).code,"approval_invalid");self.assertEqual(project_result("request-1",result("error",error,None),structured=True).error.message,"Approval is invalid.")
 def test_unknown_errors_become_internal(self):self.assertEqual(project_error(ToolError(code="SF-RUNTIME-UNKNOWN",category="runtime",message="/private/path",details={})).code,"internal")
if __name__=="__main__":unittest.main()
