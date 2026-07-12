"""Deterministic reviewed-policy evaluation without executable policy input."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from pydantic import Field, field_validator

from servicefabric_contracts import PolicyDecision, PolicyEvaluationRequest
from servicefabric_contracts.governance import (
    ApprovalRequirement,
    AuthorityGrant,
    PolicyConstraint,
    PolicyDecisionSpec,
    RiskClass,
)
from servicefabric_contracts.common import Digest, Identifier, ImmutableContractModel
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata


class PolicyEvaluationError(RuntimeError):
    """A safe fail-closed policy evaluation failure."""


class PolicyBundle(ImmutableContractModel):
    bundle_id: Identifier
    version: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    digest: Digest
    allowed_scopes: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    denied_effects: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=32)
    approval_effects: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=32)
    maximum_wall_clock_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    decision_ttl_seconds: int = Field(default=300, ge=1, le=3600)
    approval_policy_ref: Identifier = "approval-default"

    @field_validator("allowed_scopes", "denied_effects", "approval_effects")
    @classmethod
    def unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("policy values must be unique")
        return values


@dataclass(frozen=True, slots=True)
class TrustedPolicyInput:
    request: PolicyEvaluationRequest
    trusted_adapter_ref: str

    @classmethod
    def from_authenticated_adapter(cls, request: PolicyEvaluationRequest, *, adapter_ref: str) -> "TrustedPolicyInput":
        if not adapter_ref or not adapter_ref.startswith("trusted-"):
            raise PolicyEvaluationError("authenticated trusted adapter is required")
        if request.spec.caller.principal_type == "anonymous":
            raise PolicyEvaluationError("anonymous authority is denied")
        return cls(request=request, trusted_adapter_ref=adapter_ref)


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _risk(effect_types: set[str]) -> RiskClass:
    if effect_types & {"payment_initiate", "infrastructure_change"}:
        return "critical"
    if effect_types & {"database_write", "file_write", "message_send", "task_create", "human_workflow_create"}:
        return "high"
    if effect_types & {"external_read"}:
        return "moderate"
    return "low"


class VersionedPolicyEvaluator:
    def __init__(self, bundles: tuple[PolicyBundle, ...]):
        self._bundles = {(bundle.bundle_id, bundle.version): bundle for bundle in bundles}
        if len(self._bundles) != len(bundles):
            raise ValueError("policy bundle versions must be unique")

    def evaluate(self, trusted: TrustedPolicyInput, *, now: datetime) -> PolicyDecision:
        if not isinstance(trusted, TrustedPolicyInput):
            raise PolicyEvaluationError("trusted policy input is required")
        if now.tzinfo is None or now.utcoffset() is None:
            raise PolicyEvaluationError("evaluation clock must be timezone-aware")
        request = trusted.request
        spec = request.spec
        bundle = self._bundles.get((spec.policy_bundle_ref, spec.policy_version))
        if bundle is None or bundle.digest != spec.policy_digest:
            raise PolicyEvaluationError("reviewed policy version is unavailable")

        effects = {effect.effect_type for effect in spec.declared_effects}
        effect_refs = tuple(sorted(effect.replace("_", "-") for effect in effects))
        risk = _risk(effects)
        caller_scopes = set(spec.caller.scopes)
        requested_scopes = set(spec.requested_authority.scopes)
        required_scopes = {permission.permission_id for permission in spec.required_permissions}
        allowed_scopes = set(bundle.allowed_scopes)
        effective_scopes = tuple(sorted(requested_scopes & caller_scopes & allowed_scopes))

        outcome = "allow"
        reason_codes: tuple[str, ...] = ("policy-allowed",)
        safe_reason = "Reviewed policy allows the requested operation."
        authority: AuthorityGrant | None = AuthorityGrant(
            scopes=effective_scopes,
            tenant_ref=spec.requested_authority.tenant_ref,
            resource_refs=spec.requested_authority.resource_refs,
        )
        constraints: list[PolicyConstraint] = []
        approval = None

        if effects & set(bundle.denied_effects) or not required_scopes.issubset(caller_scopes & allowed_scopes):
            outcome = "deny"
            reason_codes = ("policy-denied",)
            safe_reason = "Required authority is not available."
            authority = None
            effective_budget = None
        else:
            effective_budget = spec.requested_budget.model_copy(deep=True)
            requested_ms = spec.requested_budget.maximum_wall_clock_ms
            if bundle.maximum_wall_clock_ms is not None and (requested_ms is None or requested_ms > bundle.maximum_wall_clock_ms):
                effective_budget = effective_budget.model_copy(update={"maximum_wall_clock_ms": bundle.maximum_wall_clock_ms})
                constraints.append(PolicyConstraint(constraint_id="wall-clock-limit", kind="budget", value_ref="policy-wall-clock"))
            if set(effective_scopes) != requested_scopes:
                constraints.append(PolicyConstraint(constraint_id="scope-attenuation", kind="scope", value_ref="policy-scopes"))
            if effects & set(bundle.approval_effects):
                outcome = "require_approval"
                reason_codes = ("approval-required",)
                safe_reason = "Reviewed policy requires explicit approval."
                approval = ApprovalRequirement(
                    approval_policy_ref=bundle.approval_policy_ref,
                    effect_refs=tuple(sorted(effect_refs)),
                    minimum_approver_strength="multi_factor",
                )
            elif constraints:
                outcome = "constrained_allow"
                reason_codes = ("policy-constrained",)
                safe_reason = "Reviewed policy allows attenuated authority."

        evaluation_digest = _digest(request.model_dump(mode="json", by_alias=True))
        decision_seed = {"evaluation": evaluation_digest, "policy": bundle.digest, "outcome": outcome}
        decision_id = "policy-" + hashlib.sha256(_canonical(decision_seed)).hexdigest()[:24]
        return PolicyDecision(
            apiVersion="servicefabric.ai/v1alpha1",
            kind="PolicyDecision",
            metadata=ResourceMetadata(
                id=decision_id,
                name="Deterministic policy decision",
                description="Immutable result of reviewed policy evaluation.",
                owner_ref=OwnerReference(kind="service", id="policy-evaluator"),
            ),
            spec=PolicyDecisionSpec(
                decision_id=decision_id,
                evaluation_request_ref=spec.evaluation_request_id,
                evaluation_digest=evaluation_digest,
                caller_context_digest=spec.caller_context_digest,
                tool_id=spec.tool_id,
                revision_ref=spec.revision_ref,
                intent_digest=spec.intent_digest,
                declared_effect_refs=effect_refs,
                outcome=outcome,
                risk=risk,
                policy_bundle_ref=bundle.bundle_id,
                policy_version=bundle.version,
                policy_digest=bundle.digest,
                effective_authority=authority,
                effective_budget=effective_budget,
                constraints=tuple(constraints),
                approval_requirement=approval,
                reason_codes=reason_codes,
                safe_reason=safe_reason,
                issued_at=now,
                valid_until=now + timedelta(seconds=bundle.decision_ttl_seconds),
                evaluator_ref="policy-evaluator",
            ),
        )
