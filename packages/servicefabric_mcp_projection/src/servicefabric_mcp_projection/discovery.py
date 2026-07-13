"""Caller-specific, reviewed MCP projection discovery."""
from dataclasses import dataclass
from servicefabric_contracts.caller import CallerContext
from .models import McpToolPage,ProjectedMcpTool
@dataclass(frozen=True,slots=True)
class ProjectionCandidate:
 canonical_tool_id:str;revision_ref:str;name:str;title:str;description:str;input_schema:dict;enabled:bool;available:bool;discover_scopes:tuple[str,...]=();structured_result:bool=False;progress:bool=False;cancellation:bool=False;durable_operations:bool=False;federated:bool=False
class DiscoveryService:
 def __init__(self,candidates:tuple[ProjectionCandidate,...],*,maximum_page_size:int=32):self._candidates=tuple(candidates);self._maximum_page_size=maximum_page_size
 def list_tools(self,caller:CallerContext,*,cursor:str|None=None,page_size:int=16)->McpToolPage:
  if page_size<1 or page_size>self._maximum_page_size:raise ValueError("invalid page size")
  visible=[]
  for candidate in self._candidates:
   if not candidate.enabled or not candidate.available or candidate.federated:continue
   if not set(candidate.discover_scopes).issubset(set(caller.scopes)):continue
   visible.append(ProjectedMcpTool(name=candidate.name,canonical_tool_id=candidate.canonical_tool_id,revision_ref=candidate.revision_ref,title=candidate.title,description=candidate.description,input_schema=candidate.input_schema,structured_result=candidate.structured_result,progress=candidate.progress,cancellation=candidate.cancellation,durable_operations=candidate.durable_operations))
  visible.sort(key=lambda tool:(tool.name,tool.revision_ref))
  start=0
  if cursor:
   names=[tool.name for tool in visible]
   if cursor not in names:raise ValueError("invalid discovery cursor")
   start=names.index(cursor)+1
  page=tuple(visible[start:start+page_size]);next_cursor=page[-1].name if start+page_size<len(visible) else None
  return McpToolPage(tools=page,next_cursor=next_cursor)
