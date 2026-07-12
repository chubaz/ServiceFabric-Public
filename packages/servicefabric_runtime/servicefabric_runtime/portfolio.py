import json
from pathlib import Path
from servicefabric_contracts import ToolsetDefinition
class FilePortfolio:
 def __init__(self,root:Path): self.root=root.resolve()
 def load(self,name:str)->ToolsetDefinition:
  if "/" in name or ".." in name: raise ValueError("invalid portfolio name")
  path=(self.root/f"{name}.json").resolve()
  if self.root not in path.parents: raise ValueError("portfolio escape")
  return ToolsetDefinition.model_validate_json(path.read_text(encoding="utf-8"))
 def resolve(self,toolset:str,tool_id:str):
  matches=[x for x in self.load(toolset).spec.members if x.tool_id==tool_id]
  if len(matches)!=1: raise KeyError(tool_id)
  return matches[0]
