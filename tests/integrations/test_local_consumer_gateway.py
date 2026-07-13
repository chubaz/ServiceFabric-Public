from pathlib import Path
import tempfile
import unittest

from services.local_gateway import LocalConsumerGateway


ROOT = Path(__file__).resolve().parents[2]


class LocalConsumerGatewayTests(unittest.TestCase):
    def test_research_demo_uses_canonical_runtime_and_policy(self):
        gateway = LocalConsumerGateway(ROOT / "packages" / "servicefabric_runtime" / "portfolios")
        result = gateway.invoke("research.search_papers", {"query": "retrieval", "maximum_results": 1})
        self.assertEqual(gateway.list_tools(), ("math.calculate", "research.prepare_literature_review", "research.search_papers"))
        self.assertEqual(result.data["papers"][0]["id"], "paper.retrieval-augmentation")

    def test_gateway_uses_an_explicit_workspace_root(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            gateway = LocalConsumerGateway(
                ROOT / "packages" / "servicefabric_runtime" / "portfolios",
                workspace_root=workspace,
            )
            self.assertEqual(gateway.workspace_root, workspace.resolve())
            self.assertTrue(workspace.is_dir())

    def test_approval_required_demo_is_accepted_as_a_durable_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            gateway = LocalConsumerGateway(
                ROOT / "packages" / "servicefabric_runtime" / "portfolios",
                workspace_root=Path(directory),
            )
            result = gateway.invoke("research.prepare_literature_review", {"query": "retrieval"})
            self.assertEqual(result.kind, "ToolInvocationAcceptance")
            operation, _ = gateway._operations.get_operation(result.operation_ref)
            self.assertEqual(operation.spec.state, "waiting_for_approval")
