import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/"packages/servicefabric_contracts/src"),str(ROOT/"packages/servicefabric_mcp_client")]
from servicefabric_contracts import ToolsetDefinition
from servicefabric_mcp_client import ServerConfiguration
class PortfolioTests(unittest.TestCase):
 def test_research_toolset_and_server_are_reviewed(self):
  toolset=ToolsetDefinition.model_validate_json((ROOT/"portfolio/toolsets/research-demo.json").read_text());self.assertEqual([x.tool_id for x in toolset.spec.members],["math.calculate","research.prepare_literature_review","research.search_papers"])
  config=ServerConfiguration.load(ROOT/"portfolio/external-servers/research-provider.json");self.assertEqual(len(config.allowed_tools),1)
