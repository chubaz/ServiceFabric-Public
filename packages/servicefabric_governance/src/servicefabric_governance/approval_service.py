"""Bounded approval lifecycle over immutable canonical records."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from servicefabric_contracts import ApprovalBinding, ApprovalDecision, ApprovalRequest, PolicyDecision
from servicefabric_contracts.approvals import (
    ApprovalBindingSpec,
    ApprovalDecisionSpec,
    ApprovalRequestSpec,
    ApprovalScope,
)
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata


class ApprovalError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _identifier(prefix: str, value: object) -> str:
    return prefix + "-" + hashlib.sha256(_canonical(value)).hexdigest()[:24]


def _metadata(identifier: str, name: str) -> ResourceMetadata:
    return ResourceMetadata(
        id=identifier,
        name=name,
        description="Immutable record created by the bounded approval service.",
        owner_ref=OwnerReference(kind="service", id="approval-service"),
    )


@dataclass(frozen=True, slots=True)
class TrustedApprover:
    subject_ref: str
    authority_ref: str
    authentication_strength: str

    @classmethod
    def from_authenticated_adapter(cls, *, subject_ref: str, authority_ref: str, authentication_strength: str, adapter_ref: str) -> "TrustedApprover":
        if not adapter_ref.startswith("trusted-"):
            raise ApprovalError("trusted approver adapter is required")
        if authentication_strength not in {"multi_factor", "workload", "federated"}:
            raise ApprovalError("approver authentication strength is insufficient")
        return cls(subject_ref, authority_ref, authentication_strength)


class ApprovalService:
    def __init__(self) -> None:
        self._decisions: dict[str, ApprovalDecision] = {}
        self._consumed_bindings: set[str] = set()

    def create_request(
        self,
        decision: PolicyDecision,
        *,
        request_ref: str,
        operation_ref: str,
        caller_ref: str,
        tenant_ref: str | None,
        argument_digest: str,
        effect_class: str,
        requested_authority: AuthorityGrant,
        now: datetime,
        expires_at: datetime,
    ) -> ApprovalRequest:
        if decision.spec.outcome != "require_approval" or decision.spec.approval_requirement is None:
            raise ApprovalError("policy decision does not require approval")
        if effect_class not in decision.spec.approval_requirement.effect_refs:
            raise ApprovalError("effect is outside the policy approval requirement")
        seed = {"decision": decision.spec.decision_id, "operation": operation_ref, "intent": decision.spec.intent_digest, "arguments": argument_digest}
        identifier = _identifier("approval-request", seed)
        scope = ApprovalScope(effect_refs=decision.spec.approval_requirement.effect_refs, authority=requested_authority, single_use=True)
        return ApprovalRequest(
            apiVersion="servicefabric.ai/v1alpha1", kind="ApprovalRequest", metadata=_metadata(identifier, "Approval request"),
            spec=ApprovalRequestSpec(
                approval_request_id=identifier,
                policy_decision_ref=decision.spec.decision_id,
                policy_decision_digest=_digest(decision.model_dump(mode="json", by_alias=True)),
                request_ref=request_ref,
                operation_ref=operation_ref,
                caller_ref=caller_ref,
                tenant_ref=tenant_ref,
                tool_id=decision.spec.tool_id,
                revision_ref=decision.spec.revision_ref,
                intent_digest=decision.spec.intent_digest,
                argument_digest=argument_digest,
                effect_class=effect_class,
                requested_authority=requested_authority,
                approval_scope=scope,
                risk=decision.spec.risk,
                reason=decision.spec.safe_reason or "Policy requires approval.",
                created_at=now,
                expires_at=expires_at,
            ),
        )

    def decide(self, request: ApprovalRequest, approver: TrustedApprover, *, outcome: str, now: datetime, reason_code: str, safe_reason: str) -> ApprovalDecision:
        if not isinstance(approver, TrustedApprover):
            raise ApprovalError("trusted approver context is required")
        if outcome not in {"approved", "denied", "expired"}:
            raise ApprovalError("unsupported approval outcome")
        if request.spec.approval_request_id in self._decisions:
            raise ApprovalError("approval request already has a decision")
        if outcome == "approved" and now >= request.spec.expires_at:
            raise ApprovalError("expired approval request cannot be approved")
        identifier = _identifier("approval-decision", {"request": request.spec.approval_request_id, "outcome": outcome, "time": now.isoformat()})
        decision = ApprovalDecision(
            apiVersion="servicefabric.ai/v1alpha1", kind="ApprovalDecision", metadata=_metadata(identifier, "Approval decision"),
            spec=ApprovalDecisionSpec(
                approval_decision_id=identifier,
                approval_request_ref=request.spec.approval_request_id,
                approval_request_digest=_digest(request.model_dump(mode="json", by_alias=True)),
                policy_decision_ref=request.spec.policy_decision_ref,
                intent_digest=request.spec.intent_digest,
                outcome=outcome,
                approver_subject_ref=approver.subject_ref,
                approver_authority_ref=approver.authority_ref,
                decided_at=now,
                valid_until=request.spec.expires_at if outcome == "approved" else None,
                supersedes_decision_ref="expired-pending-decision" if outcome == "expired" else None,
                reason_code=reason_code,
                safe_reason=safe_reason,
            ),
        )
        self._decisions[request.spec.approval_request_id] = decision
        return decision

    def revoke(self, request: ApprovalRequest, prior: ApprovalDecision, approver: TrustedApprover, *, now: datetime, safe_reason: str) -> ApprovalDecision:
        if prior.spec.outcome != "approved" or prior.spec.approval_request_ref != request.spec.approval_request_id:
            raise ApprovalError("only the matching approved decision can be revoked")
        identifier = _identifier("approval-revocation", {"prior": prior.spec.approval_decision_id, "time": now.isoformat()})
        return ApprovalDecision(
            apiVersion="servicefabric.ai/v1alpha1", kind="ApprovalDecision", metadata=_metadata(identifier, "Approval revocation"),
            spec=ApprovalDecisionSpec(
                approval_decision_id=identifier,
                approval_request_ref=request.spec.approval_request_id,
                approval_request_digest=_digest(request.model_dump(mode="json", by_alias=True)),
                policy_decision_ref=request.spec.policy_decision_ref,
                intent_digest=request.spec.intent_digest,
                outcome="revoked",
                approver_subject_ref=approver.subject_ref,
                approver_authority_ref=approver.authority_ref,
                decided_at=now,
                supersedes_decision_ref=prior.spec.approval_decision_id,
                reason_code="approval-revoked",
                safe_reason=safe_reason,
            ),
        )

    def bind(self, request: ApprovalRequest, decision: ApprovalDecision, *, policy_version: str) -> ApprovalBinding:
        if decision.spec.outcome != "approved" or decision.spec.approval_request_ref != request.spec.approval_request_id:
            raise ApprovalError("matching approved decision is required")
        seed = {"request": request.spec.approval_request_id, "decision": decision.spec.approval_decision_id, "intent": request.spec.intent_digest}
        identifier = _identifier("approval-binding", seed)
        return ApprovalBinding(
            apiVersion="servicefabric.ai/v1alpha1", kind="ApprovalBinding", metadata=_metadata(identifier, "Approval binding"),
            spec=ApprovalBindingSpec(
                binding_id=identifier,
                approval_request_ref=request.spec.approval_request_id,
                approval_decision_ref=decision.spec.approval_decision_id,
                approval_decision_digest=_digest(decision.model_dump(mode="json", by_alias=True)),
                policy_decision_ref=request.spec.policy_decision_ref,
                policy_version=policy_version,
                caller_ref=request.spec.caller_ref,
                tenant_ref=request.spec.tenant_ref,
                operation_ref=request.spec.operation_ref,
                tool_id=request.spec.tool_id,
                revision_ref=request.spec.revision_ref,
                intent_digest=request.spec.intent_digest,
                argument_digest=request.spec.argument_digest,
                effect_class=request.spec.effect_class,
                authority_scope=request.spec.approval_scope,
                valid_from=decision.spec.decided_at,
                valid_until=decision.spec.valid_until,
                binding_digest=_digest(seed),
            ),
        )

    def validate_binding(self, binding: ApprovalBinding, *, caller_ref: str, revision_ref: str, intent_digest: str, argument_digest: str, now: datetime, consume: bool = False) -> None:
        if not binding.spec.matches_intent(caller_ref=caller_ref, revision_ref=revision_ref, intent_digest=intent_digest, argument_digest=argument_digest):
            raise ApprovalError("approval binding does not match execution intent")
        if now < binding.spec.valid_from or now >= binding.spec.valid_until:
            raise ApprovalError("approval binding is not currently valid")
        if binding.spec.binding_id in self._consumed_bindings:
            raise ApprovalError("single-use approval binding was already consumed")
        if consume and binding.spec.authority_scope.single_use:
            self._consumed_bindings.add(binding.spec.binding_id)
