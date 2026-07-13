"""Local consumer gateway boundary for the reviewed research-demo toolset."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from servicefabric_contracts import OperationEvent, ServiceFabricOperation, ToolInvocationAcceptance, ToolInvocationRequest
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.caller import CallerContext
from servicefabric_contracts.effects import EffectDeclaration
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_contracts.invocation import RevisionInvocationTarget
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata
from servicefabric_contracts.durable_operations import OperationEventSpec
from servicefabric_contracts.operations import CancellationState
from servicefabric_contracts.permissions import PermissionRequirement
from servicefabric_contracts.protocol import ProtocolContext
from servicefabric_governance import GovernedInvocationBoundary, InvocationGovernanceProfile, PolicyBundle, VersionedPolicyEvaluator, ApprovalService
from servicefabric_governance_service import create_governance_operations_service
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
            InvocationGovernanceProfile("research.prepare_literature_review", "1.0.0", (EffectDeclaration(effect_type="task_create", target_category="research", scope="local_fixture", reversibility="reversible", verification_required=True, approval_required=True, idempotency_required=True),), (PermissionRequirement(permission_id="research-search", tenant_scope="caller_tenant", resource_scope="local"),), AuthorityGrant(scopes=("research-search",), tenant_ref="local"), ExecutionBudget(), "moderate", "research-demo-policy", "1.0.0", bundle.digest, durable=True),
        )
        # The local evaluator's approval rule is explicit and still evaluated by V3.
        approval_bundle = PolicyBundle(bundle_id=bundle.bundle_id, version=bundle.version, digest=bundle.digest, allowed_scopes=bundle.allowed_scopes, approval_effects=("task_create",))
        self._operations = create_governance_operations_service(root=self.workspace_root, evaluator=VersionedPolicyEvaluator((approval_bundle,)))
        self._boundary = GovernedInvocationBoundary(evaluator=VersionedPolicyEvaluator((approval_bundle,)), approvals=self._operations.approvals, runtime=runtime, profiles=profiles, approval_lookup=self._operations.approval_binding, approval_required_acceptor=self._accept_for_approval)

    def list_tools(self) -> tuple[str, ...]:
        return ("math.calculate", "research.prepare_literature_review", "research.search_papers")

    def invoke(self, tool_id: str, arguments: dict[str, object]):
        revision = "1.0.0"
        now = datetime.now(timezone.utc)
        scopes = ("math-calculate",) if tool_id == "math.calculate" else ("research-search",)
        request = ToolInvocationRequest(apiVersion="servicefabric.ai/v1alpha1", kind="ToolInvocationRequest", metadata=ResourceMetadata(id="gateway-request-" + tool_id.replace(".", "-"), name="Local consumer request", description="Canonical request received by the local gateway.", owner_ref=OwnerReference(kind="service", id="local-consumer-gateway")), spec={"request_id": "gateway-request-" + tool_id.replace(".", "-"), "target": RevisionInvocationTarget(target_kind="revision", tool_id=tool_id, revision_ref=revision), "arguments": arguments, "caller_context": CallerContext(subject_ref="local-consumer", principal_type="human", tenant_ref="local", issuer="servicefabric-local", scopes=scopes, authentication_strength="multi_factor"), "protocol_context": ProtocolContext(protocol="internal", adapter_ref="trusted-local-gateway"), "budget": ExecutionBudget(), "requested_response_mode": "synchronous"})
        return self._boundary.invoke(request, trusted_adapter_ref="trusted-local-gateway", now=now)

    def _accept_for_approval(self, request, decision, intent_digest, argument_digest, now):
        """Persist an approval-gated operation through the V3 operation facade."""
        operation_id = "operation-" + hashlib.sha256(intent_digest.encode("ascii")).hexdigest()[:24]
        operation = ServiceFabricOperation(
            apiVersion="servicefabric.ai/v1alpha1", kind="ServiceFabricOperation",
            metadata=ResourceMetadata(id=operation_id, name="Literature review", description="Approval-gated local research operation.", owner_ref=OwnerReference(kind="service", id="local-consumer-gateway")),
            spec={"operation_id": operation_id, "request_ref": request.spec.request_id, "invocation_ref": request.spec.request_id, "tool_id": request.spec.target.tool_id, "revision_ref": request.spec.target.revision_ref, "state":"accepted", "created_at":now, "updated_at":now, "cancellation":CancellationState(cancellable=True)},
        )
        event_digest = "sha256:" + hashlib.sha256(json.dumps({"operation":operation_id,"event":"accepted"}, sort_keys=True).encode()).hexdigest()
        event = OperationEvent(apiVersion="servicefabric.ai/v1alpha1", kind="OperationEvent", metadata=ResourceMetadata(id="event-"+operation_id, name="Operation accepted", description="Initial immutable operation event.", owner_ref=OwnerReference(kind="service", id="local-consumer-gateway")), spec=OperationEventSpec(event_id="event-"+operation_id, operation_ref=operation_id, sequence=1, operation_version=1, event_type="accepted", recorded_at=now, event_digest=event_digest))
        submission = self._operations.submit_operation(operation, event, key_digest=intent_digest, intent_digest=intent_digest, caller_ref=request.spec.caller_context.subject_ref, namespace_ref=request.spec.caller_context.tenant_ref, now=now, expires_at=now.replace(year=now.year + 1))
        if submission.outcome == "accepted":
            self._operations.transition(operation_id, "waiting_for_approval", expected_version=1, now=now, actor_ref="local-consumer-gateway", reason_code="approval-required", safe_reason="Policy requires local trusted-development approval.")
            self._operations.create_approval_request(decision, request_ref=request.spec.request_id, operation_ref=operation_id, caller_ref=request.spec.caller_context.subject_ref, tenant_ref=request.spec.caller_context.tenant_ref, argument_digest=argument_digest, effect_class="task-create", requested_authority=decision.spec.effective_authority, now=now, expires_at=now.replace(year=now.year + 1))
        return ToolInvocationAcceptance(apiVersion="servicefabric.ai/v1alpha1", kind="ToolInvocationAcceptance", request_id=request.spec.request_id, invocation_id=request.spec.request_id, operation_ref=submission.operation_ref, accepted_at=now, status="accepted")
