from __future__ import annotations
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FORBIDDEN={"django","flask","fastapi","sqlalchemy","subprocess","socket","requests","httpx","docker","kubernetes","servicefabric_mcp_client"}
class McpProjectionBoundaryTests(unittest.TestCase):
 def test_projection_and_gateway_contain_no_domain_or_network_implementation(self):
  for root in (ROOT/"packages/servicefabric_mcp_projection/src",ROOT/"packages/servicefabric_mcp_harness/src",ROOT/"services/mcp_gateway/src"):
   for path in root.rglob("*.py"):
    tree=ast.parse(path.read_text(encoding="utf-8"));imports=set()
    for node in ast.walk(tree):
     if isinstance(node,ast.Import):imports|={item.name.split(".")[0] for item in node.names}
     elif isinstance(node,ast.ImportFrom) and node.module:imports.add(node.module.split(".")[0])
    self.assertFalse(imports&FORBIDDEN,f"{path}: {imports&FORBIDDEN}")
 def test_canonical_contracts_do_not_import_mcp_projection(self):
  root=ROOT/"packages/servicefabric_contracts/src/servicefabric_contracts"
  for path in root.glob("*.py"):self.assertNotIn("servicefabric_mcp",path.read_text(encoding="utf-8"))
 def test_gateway_client_does_not_access_durable_storage(self):
  source=(ROOT/"clients/python/servicefabric_client/mcp.py").read_text(encoding="utf-8")
  self.assertNotIn("servicefabric_operations",source);self.assertNotIn("Path(",source);self.assertNotIn("open(",source)
