from __future__ import annotations

from pathlib import Path
import unittest

from servicefabric_contracts import ToolInvocationRequest
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.caller import CallerContext
from servicefabric_contracts.invocation import RevisionInvocationTarget
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata
from servicefabric_contracts.protocol import ProtocolContext
from servicefabric_runtime import FilePortfolio, InvocationKernel


ROOT = Path(__file__).resolve().parents[2]


class ResearchDemoRuntimeTests(unittest.TestCase):
    def test_research_search_papers_uses_deterministic_local_fixture(self) -> None:
        request = ToolInvocationRequest(
            apiVersion="servicefabric.ai/v1alpha1",
            kind="ToolInvocationRequest",
            metadata=ResourceMetadata(
                id="request.research-demo",
                name="Research demo request",
                description="Deterministic test request.",
                owner_ref=OwnerReference(kind="test", id="runtime"),
            ),
            spec={
                "request_id": "request.research-demo",
                "target": RevisionInvocationTarget(
                    target_kind="revision",
                    tool_id="research.search_papers",
                    revision_ref="1.0.0",
                ),
                "arguments": {"query": "retrieval augmented generation", "maximum_results": 1},
                "caller_context": CallerContext(
                    subject_ref="test-user",
                    principal_type="human",
                    issuer="servicefabric-test",
                    authentication_strength="multi_factor",
                ),
                "protocol_context": ProtocolContext(protocol="internal", adapter_ref="trusted-test"),
                "budget": ExecutionBudget(),
                "requested_response_mode": "synchronous",
            },
        )

        result = InvocationKernel(
            FilePortfolio(ROOT / "packages" / "servicefabric_runtime" / "portfolios")
        ).invoke(request, toolset="research-demo")

        self.assertEqual(result.status, "success")
        self.assertEqual(result.data["papers"][0]["id"], "paper.retrieval-augmentation")
