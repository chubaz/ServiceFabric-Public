from datetime import datetime,timezone
from servicefabric_contracts import ToolResult
from .math_tool import calculate
from .research_tool import search_papers
class InvocationKernel:
 def __init__(self,portfolio):self.portfolio=portfolio
 def invoke(self,request,toolset="core-tools"):
  member=self.portfolio.resolve(toolset,request.spec.target.tool_id)
  if getattr(request.spec.target,"revision_ref",member.revision_ref)!=member.revision_ref: raise ValueError("revision mismatch")
  handlers={"math.calculate":calculate,"research.search_papers":search_papers}
  handler=handlers.get(member.tool_id)
  if handler is None:raise KeyError(member.tool_id)
  started=datetime.now(timezone.utc);data=handler(request.spec.arguments);completed=datetime.now(timezone.utc)
  return ToolResult(apiVersion="servicefabric.ai/v1alpha1",kind="ToolResult",status="success",invocation_id=request.spec.request_id,tool_id=member.tool_id,revision_ref=member.revision_ref,started_at=started,completed_at=completed,duration=completed-started,data=data)
