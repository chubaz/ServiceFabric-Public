"""Remote consumer client for the bounded local ServiceFabric gateway."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen

from servicefabric_contracts import ToolResult


class RemoteServiceFabricClient:
    def __init__(self, endpoint: str, *, toolset: str = "research-demo"):
        if not endpoint.startswith("http://127.0.0.1:"):
            raise ValueError("only loopback gateway endpoints are supported")
        self.endpoint = endpoint.rstrip("/")
        self.toolset = toolset

    def list_tools(self) -> tuple[str, ...]:
        with urlopen(f"{self.endpoint}/v1/toolsets/{self.toolset}/tools", timeout=5) as response:
            return tuple(json.loads(response.read())["tools"])

    def invoke(self, tool_id: str, arguments: dict[str, object]) -> ToolResult:
        request = Request(f"{self.endpoint}/v1/toolsets/{self.toolset}/tools/{tool_id}:invoke", data=json.dumps({"arguments": arguments}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=10) as response:
            return ToolResult.model_validate(json.loads(response.read()))
