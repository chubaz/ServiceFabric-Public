from pathlib import Path
import unittest
from servicefabric_client.connection import RemoteServiceFabricClient
from services.local_gateway import LocalConsumerGateway, LoopbackGatewayServer

ROOT = Path(__file__).resolve().parents[2]

class LoopbackConsumerConnectionTests(unittest.TestCase):
 def test_remote_client_uses_gateway_for_research_demo(self):
  gateway=LocalConsumerGateway(ROOT/"packages/servicefabric_runtime"/"portfolios")
  with LoopbackGatewayServer(gateway) as server:
   client=RemoteServiceFabricClient(server.endpoint)
   self.assertIn("research.search_papers",client.list_tools())
   self.assertEqual(client.invoke("research.search_papers",{"query":"retrieval","maximum_results":1}).data["papers"][0]["id"],"paper.retrieval-augmentation")
