from __future__ import annotations
from pathlib import Path
from servicefabric_agentic_contracts import AgentToolResult

class BoundedAgentTools:
    """Allowlisted inspection only; capability use is supplied by a public facade."""
    def __init__(self, repository: str | Path, capability_facade: object | None = None): self.root = Path(repository).resolve(); self.facade = capability_facade
    def invoke(self, name: str, arguments: dict) -> AgentToolResult:
        if name == "workspace.inspect":
            relative = arguments.get("path", "."); target = (self.root / relative).resolve()
            if target != self.root and self.root not in target.parents: return AgentToolResult(status="blocked", summary="path escapes repository")
            return AgentToolResult(status="success", summary="workspace path inspected", data={"path": str(target), "exists": target.exists()})
        if name == "capabilities.discover" and self.facade is not None:
            application_id = arguments["application_id"]; return AgentToolResult(status="success", summary="capabilities discovered", data={"capabilities": self.facade.discover(application_id)})
        return AgentToolResult(status="blocked", summary="tool is not allowlisted")
