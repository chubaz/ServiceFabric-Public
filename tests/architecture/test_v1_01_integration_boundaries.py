import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class IntegrationBoundaryTests(unittest.TestCase):
 def test_contracts_and_runtime_do_not_import_integration_packages(self):
  forbidden={"servicefabric_mcp_client","servicefabric_langchain","langchain","langgraph","mcp"}
  for root in (ROOT/"packages/servicefabric_contracts/src",ROOT/"packages/servicefabric_runtime"):
   for path in root.rglob("*.py"):
    imported=set()
    for node in ast.walk(ast.parse(path.read_text())):
     if isinstance(node,ast.Import):imported.update(x.name.split('.')[0] for x in node.names)
     elif isinstance(node,ast.ImportFrom) and node.module:imported.add(node.module.split('.')[0])
    self.assertFalse(imported & forbidden,path)
 def test_no_servicefabric_mcp_server_or_gateway(self):
  for path in (ROOT/"packages/servicefabric_mcp_client").rglob("*.py"):
   text=path.read_text();self.assertNotIn("tools/list",text);self.assertNotIn("tools/call",text);self.assertNotIn("McpServer",text)
