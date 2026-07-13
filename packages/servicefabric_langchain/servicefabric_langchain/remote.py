"""LangGraph-compatible wrappers over the remote ServiceFabric client."""

from __future__ import annotations


class RemoteServiceFabricTool:
    def __init__(self, client, tool_id: str):
        self.client = client
        self.tool_id = tool_id
        self.name = tool_id.replace(".", "_")

    def invoke(self, arguments: dict[str, object]) -> dict[str, object]:
        result = self.client.invoke(self.tool_id, arguments)
        if result.status == "error":
            raise RuntimeError(result.error.message)
        return result.data


class RemoteResearchDemoLoader:
    def __init__(self, client):
        self.client = client

    def load_tools(self):
        return [RemoteServiceFabricTool(self.client, tool_id) for tool_id in self.client.list_tools()]
