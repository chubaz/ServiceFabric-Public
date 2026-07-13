"""Installation and construction checks for local service boundaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_application_builder import create_application_builder_service
from servicefabric_capsule_host import create_capsule_host_service
from servicefabric_governance import PolicyBundle, VersionedPolicyEvaluator
from servicefabric_governance_service import create_governance_operations_service
from servicefabric_runtime import FilePortfolio, InvocationKernel
from servicefabric_tool_runtime_service import ToolRuntimeService


ROOT = Path(__file__).resolve().parents[2]


class LocalServicePackagingTests(unittest.TestCase):
    def test_application_and_capsule_services_construct_from_reviewed_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            builder = create_application_builder_service(
                portfolio_root=ROOT / "portfolio" / "applications",
                artifact_store_root=root / "artifacts",
            )
            capsule = create_capsule_host_service(
                capsule_portfolio_root=ROOT / "portfolio" / "capsules",
                application_portfolio_root=ROOT / "portfolio" / "applications",
                artifact_store_root=root / "artifacts",
            )

            self.assertEqual(builder.list_applications(), ("examples.hello-static",))
            self.assertEqual(capsule.application_portfolio.root, ROOT / "portfolio" / "applications")

    def test_governance_service_constructs_its_durable_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evaluator = VersionedPolicyEvaluator(
                (
                    PolicyBundle(
                        bundle_id="local-policy",
                        version="1.0.0",
                        digest="sha256:" + "a" * 64,
                        allowed_scopes=("math-calculate",),
                    ),
                )
            )
            service = create_governance_operations_service(
                root=Path(temporary), evaluator=evaluator
            )

            self.assertIsNotNone(service)

    def test_runtime_service_constructs_from_the_canonical_kernel(self) -> None:
        portfolio = FilePortfolio(ROOT / "packages" / "servicefabric_runtime" / "portfolios")

        runtime = ToolRuntimeService(InvocationKernel(portfolio), toolset="research-demo")

        self.assertEqual(runtime.toolset, "research-demo")
