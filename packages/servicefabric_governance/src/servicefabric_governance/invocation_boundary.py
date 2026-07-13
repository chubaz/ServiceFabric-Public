"""Governance-aware canonical invocation boundary shared by protocol adapters."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from servicefabric_contracts import ApprovalBinding, PolicyDecision, PolicyEvaluationRequest, ToolInvocationAcceptance, ToolInvocationRequest, ToolResult
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.effects import EffectDeclaration
from servicefabric_contracts.errors import ToolError
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata
from servicefabric_contracts.permissions import PermissionRequirement

from .approval_service import ApprovalService
from .policy import TrustedPolicyInput, VersionedPolicyEvaluator


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class InvocationGovernanceProfile:
    tool_id: str
    revision_ref: str
    declared_effects: tuple[EffectDeclaration, ...]
    required_permissions: tuple[PermissionRequirement, ...]
    requested_authority: AuthorityGrant
    requested_budget: ExecutionBudget
    risk_hint: str
    policy_bundle_ref: str
    policy_version: str
    policy_digest: str
    durable: bool = False


class GovernedInvocationError(RuntimeError):
    pass


class GovernedInvocationBoundary:
    """Evaluates V3 policy before calling a canonical runtime or durable service."""

    def __init__(
        self,
        *,
        evaluator: VersionedPolicyEvaluator,
        approvals: ApprovalService,
        runtime: object,
        profiles: tuple[InvocationGovernanceProfile, ...],
        approval_lookup: Callable[[str], ApprovalBinding | None] = lambda _ref: None,
        durable_acceptor: Callable[[ToolInvocationRequest, str, datetime], ToolInvocationAcceptance] | None = None,
    ) -> None:
        self._evaluator = evaluator
        self._approvals = approvals
        self._runtime = runtime
        self._profiles = {(profile.tool_id, profile.revision_ref): profile for profile in profiles}
        if len(self._profiles) != len(profiles):
            raise ValueError("invocation governance profiles must be unique")
        self._approval_lookup = approval_lookup
        self._durable_acceptor = durable_acceptor

    def invoke(self, request: ToolInvocationRequest, *, trusted_adapter_ref: str, now: datetime) -> ToolResult | ToolInvocationAcceptance:
        target = request.spec.target
        revision_ref = getattr(target, "revision_ref", None)
        profile = self._profiles.get((target.tool_id, revision_ref))
        if profile is None:
            raise GovernedInvocationError("no reviewed governance profile exists for the immutable revision")
        intent_digest = _digest({"tool": target.tool_id, "revision": revision_ref, "caller": request.spec.caller_context.subject_ref, "arguments": request.spec.arguments})
        argument_digest = _digest(request.spec.arguments)
        policy_request = PolicyEvaluationRequest(
            apiVersion="servicefabric.ai/v1alpha1", kind="PolicyEvaluationRequest",
            metadata=ResourceMetadata(id="policy-evaluation-" + request.spec.request_id, name="Policy evaluation", description="Trusted canonical invocation policy input.", owner_ref=OwnerReference(kind="service", id="governed-invocation")),
            spec={"evaluation_request_id": "policy-evaluation-" + request.spec.request_id, "request_ref": request.spec.request_id, "request_digest": _digest(request.model_dump(mode="json", by_alias=True)), "caller": request.spec.caller_context, "caller_context_digest": _digest(request.spec.caller_context.model_dump(mode="json")), "tool_id": target.tool_id, "revision_ref": revision_ref, "intent_digest": intent_digest, "declared_effects": profile.declared_effects, "required_permissions": profile.required_permissions, "requested_authority": profile.requested_authority, "requested_budget": profile.requested_budget, "risk_hint": profile.risk_hint, "policy_bundle_ref": profile.policy_bundle_ref, "policy_version": profile.policy_version, "policy_digest": profile.policy_digest, "evaluated_at": now},
        )
        decision = self._evaluator.evaluate(TrustedPolicyInput.from_authenticated_adapter(policy_request, adapter_ref=trusted_adapter_ref), now=now)
        if decision.spec.outcome == "deny":
            return self._error_result(request, "SF-AUTHZ-DENIED", "authorization", "The requested operation is not authorized.", now)
        if decision.spec.outcome == "require_approval":
            binding = self._resolve_binding(request)
            if binding is None:
                return self._error_result(request, "SF-APPROVAL-REQUIRED", "approval", "Approval is required before execution.", now)
            try:
                self._approvals.validate_binding(binding, caller_ref=request.spec.caller_context.subject_ref, revision_ref=revision_ref, intent_digest=intent_digest, argument_digest=argument_digest, now=now, consume=True)
            except Exception:
                return self._error_result(request, "SF-APPROVAL-INVALID", "approval", "The supplied approval is not valid for this execution.", now)
        if profile.durable:
            if self._durable_acceptor is None:
                raise GovernedInvocationError("reviewed durable operation boundary is unavailable")
            return self._durable_acceptor(request, intent_digest, now)
        return self._runtime.invoke(request)

    def _resolve_binding(self, request: ToolInvocationRequest) -> ApprovalBinding | None:
        if len(request.spec.approval_refs) != 1:
            return None
        return self._approval_lookup(request.spec.approval_refs[0])

    @staticmethod
    def _error_result(request: ToolInvocationRequest, code: str, category: str, message: str, now: datetime) -> ToolResult:
        return ToolResult(apiVersion="servicefabric.ai/v1alpha1", kind="ToolResult", status="error", invocation_id=request.spec.request_id, tool_id=request.spec.target.tool_id, revision_ref=getattr(request.spec.target, "revision_ref", "unresolved"), started_at=now, completed_at=now, duration=timedelta(), data=None, error=ToolError(code=code, category=category, message=message, details={}))
