import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"packages/servicefabric_mcp_client"))
from servicefabric_mcp_client import FederatedMcpAdapter,FakeMcpTransport
from servicefabric_mcp_client.configuration import AllowedTool,ServerConfiguration
from servicefabric_mcp_client.errors import SchemaDriftError
from servicefabric_mcp_client.schema import schema_digest
class McpTests(unittest.TestCase):
 def setup(self,digest=None):
  schema={"type":"object","properties":{"query":{"type":"string"}},"required":["query"]};config=ServerConfiguration("research","streamable_http","endpoint:research",None,(AllowedTool("search_papers","research.search_papers",digest or schema_digest(schema)),));transport=FakeMcpTransport({"search_papers":{"inputSchema":schema}},{"search_papers":{"structuredContent":{"papers":[]}}});return FederatedMcpAdapter(config,transport)
 def test_allowlist_and_call(self):self.assertEqual(self.setup().invoke("research.search_papers",{"query":"x"})["data"],{"papers":[]})
 def test_schema_drift_and_unknown_tool_rejected(self):
  with self.assertRaises(SchemaDriftError):self.setup("sha256:"+"0"*64).invoke("research.search_papers",{})
  with self.assertRaises(KeyError):self.setup().invoke("unknown.tool",{})
