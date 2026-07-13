"""Typed client delegation to the inbound MCP gateway service."""
class McpGatewayClient:
 def __init__(self,gateway):self._gateway=gateway
 def initialize(self,**kwargs):return self._gateway.initialize(**kwargs)
 def list_tools(self,**kwargs):return self._gateway.list_tools(**kwargs)
 def call(self,**kwargs):return self._gateway.call(**kwargs)
