"""Local consumer gateway boundary for the reviewed research-demo toolset."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from servicefabric_contracts import ToolInvocationRequest
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.caller import CallerContext
from servicefabric_contracts.effects import EffectDeclaration
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_contracts.invocation import RevisionInvocationTarget
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata
from servicefabric_contracts.permissions import PermissionRequirement
from servicefabric_contracts.protocol import ProtocolContext
from servicefabric_governance import GovernedInvocationBoundary, InvocationGovernanceProfile, PolicyBundle, VersionedPolicyEvaluator, ApprovalService
from servicefabric_runtime import FilePortfolio, InvocationKernel
from servicefabric_tool_runtime_service import ToolRuntimeService


class LocalConsumerGateway:
    """Trusted local boundary; consumers never import tool implementations."""

    def __init__(self, portfolio_root, *, workspace_root: Path | None = None):
        # The gateway's durable state is deliberately rooted in an explicit local workspace.
        self.workspace_root = (workspace_root or Path(".servicefabric")).resolve(strict=False)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        runtime = ToolRuntimeService(InvocationKernel(FilePortfolio(portfolio_root)), toolset="research-demo")
        bundle = PolicyBundle(bundle_id="research-demo-policy", version="1.0.0", digest="sha256:" + "b" * 64, allowed_scopes=("math-calculate", "research-search"))
        profiles = (
            InvocationGovernanceProfile("math.calculate", "1.0.0", (EffectDeclaration(effect_type="none", target_category="calculation", scope="local", reversibility="not_applicable", verification_required=False, approval_required=False, idempotency_required=False),), (PermissionRequirement(permission_id="math-calculate", tenant_scope="caller_tenant", resource_scope="local"),), AuthorityGrant(scopes=("math-calculate",), tenant_ref="local"), ExecutionBudget(), "low", "research-demo-policy", "1.0.0", bundle.digest),
            InvocationGovernanceProfile("research.search_papers", "1.0.0", (EffectDeclaration(effect_type="external_read", target_category="research", scope="local_fixture", reversibility="not_applicable", verification_required=False, approval_required=False, idempotency_required=False),), (PermissionRequirement(permission_id="research-search", tenant_scope="caller_tenant", resource_scope="local"),), AuthorityGrant(scopes=("research-search",), tenant_ref="local"), ExecutionBudget(), "moderate", "research-demo-policy", "1.0.0", bundle.digest),
        )
        self._boundary = GovernedInvocationBoundary(evaluator=VersionedPolicyEvaluator((bundle,)), approvals=ApprovalService(), runtime=runtime, profiles=profiles)

    def list_tools(self) -> tuple[str, ...]:
        return ("math.calculate", "research.search_papers")

    def invoke(self, tool_id: str, arguments: dict[str, object]):
        revision = "1.0.0"
        now = datetime.now(timezone.utc)
        scopes = ("math-calculate",) if tool_id == "math.calculate" else ("research-search",)
        request = ToolInvocationRequest(apiVersion="servicefabric.ai/v1alpha1", kind="ToolInvocationRequest", metadata=ResourceMetadata(id="gateway-request-" + tool_id.replace(".", "-"), name="Local consumer request", description="Canonical request received by the local gateway.", owner_ref=OwnerReference(kind="service", id="local-consumer-gateway")), spec={"request_id": "gateway-request-" + tool_id.replace(".", "-"), "target": RevisionInvocationTarget(target_kind="revision", tool_id=tool_id, revision_ref=revision), "arguments": arguments, "caller_context": CallerContext(subject_ref="local-consumer", principal_type="human", tenant_ref="local", issuer="servicefabric-local", scopes=scopes, authentication_strength="multi_factor"), "protocol_context": ProtocolContext(protocol="internal", adapter_ref="trusted-local-gateway"), "budget": ExecutionBudget(), "requested_response_mode": "synchronous"})
        return self._boundary.invoke(request, trusted_adapter_ref="trusted-local-gateway", now=now)
