from pathlib import Path
import unittest

from services.local_gateway import LocalConsumerGateway


ROOT = Path(__file__).resolve().parents[2]


class LocalConsumerGatewayTests(unittest.TestCase):
    def test_research_demo_uses_canonical_runtime_and_policy(self):
        gateway = LocalConsumerGateway(ROOT / "packages" / "servicefabric_runtime" / "portfolios")
        result = gateway.invoke("research.search_papers", {"query": "retrieval", "maximum_results": 1})
        self.assertEqual(gateway.list_tools(), ("math.calculate", "research.search_papers"))
        self.assertEqual(result.data["papers"][0]["id"], "paper.retrieval-augmentation")
