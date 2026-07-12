"""Immutable policy-evaluation inputs and decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .budgets import ExecutionBudget
from .caller import CallerContext
from .common import Digest, Identifier, ImmutableContractModel, ToolIdentifier
from .effects import EffectDeclaration
from .metadata import ResourceMetadata
from .permissions import PermissionRequirement


RiskClass = Literal["low", "moderate", "high", "critical"]
PolicyOutcome = Literal["allow", "deny", "require_approval", "constrained_allow"]


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return value
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


class AuthorityGrant(ImmutableContractModel):
    scopes: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    tenant_ref: Identifier | None = None
    resource_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)

    @field_validator("scopes", "resource_refs")
    @classmethod
    def unique_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("authority references must be unique")
        return values


class PolicyConstraint(ImmutableContractModel):
    constraint_id: Identifier
    kind: Literal["scope", "resource", "budget", "effect", "tenant"]
    value_ref: Identifier


class ApprovalRequirement(ImmutableContractModel):
    approval_policy_ref: Identifier
    effect_refs: tuple[Identifier, ...] = Field(min_length=1, max_length=32)
    minimum_approver_strength: Literal["single_factor", "multi_factor", "workload", "federated"]


class PolicyEvaluationRequestSpec(ImmutableContractModel):
    evaluation_request_id: Identifier
    request_ref: Identifier
    request_digest: Digest
    caller: CallerContext
    caller_context_digest: Digest
    tool_id: ToolIdentifier
    revision_ref: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9][a-z0-9._:-]+$")
    operation_ref: Identifier | None = None
    intent_digest: Digest
    declared_effects: tuple[EffectDeclaration, ...] = Field(min_length=1, max_length=32)
    required_permissions: tuple[PermissionRequirement, ...] = Field(default_factory=tuple, max_length=64)
    requested_authority: AuthorityGrant
    requested_budget: ExecutionBudget
    risk_hint: RiskClass
    policy_bundle_ref: Identifier
    policy_version: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    policy_digest: Digest
    evaluated_at: datetime
    valid_until: datetime | None = None

    _aware_evaluated_at = field_validator("evaluated_at")(_aware)
    _aware_valid_until = field_validator("valid_until")(_aware)

    @field_validator("revision_ref")
    @classmethod
    def immutable_revision(cls, value: str) -> str:
        if value in {"latest", "current", "production"}:
            raise ValueError("policy evaluation requires an immutable revision")
        return value

    @model_validator(mode="after")
    def valid_window(self) -> "PolicyEvaluationRequestSpec":
        if self.valid_until is not None and self.valid_until <= self.evaluated_at:
            raise ValueError("valid_until must follow evaluated_at")
        effect_refs = [effect.effect_type for effect in self.declared_effects]
        if len(set(effect_refs)) != len(effect_refs):
            raise ValueError("declared effects must be unique")
        return self


class PolicyEvaluationRequest(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["PolicyEvaluationRequest"]
    metadata: ResourceMetadata
    spec: PolicyEvaluationRequestSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}


class PolicyDecisionSpec(ImmutableContractModel):
    decision_id: Identifier
    evaluation_request_ref: Identifier
    evaluation_digest: Digest
    caller_context_digest: Digest
    tool_id: ToolIdentifier
    revision_ref: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9][a-z0-9._:-]+$")
    intent_digest: Digest
    declared_effect_refs: tuple[Identifier, ...] = Field(min_length=1, max_length=32)
    outcome: PolicyOutcome
    risk: RiskClass
    policy_bundle_ref: Identifier
    policy_version: str = Field(min_length=1, max_length=64)
    policy_digest: Digest
    effective_authority: AuthorityGrant | None = None
    effective_budget: ExecutionBudget | None = None
    constraints: tuple[PolicyConstraint, ...] = Field(default_factory=tuple, max_length=64)
    approval_requirement: ApprovalRequirement | None = None
    reason_codes: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=16)
    safe_reason: str | None = Field(default=None, max_length=1000)
    issued_at: datetime
    valid_until: datetime | None = None
    evaluator_ref: Identifier
    evidence_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)

    _aware_issued_at = field_validator("issued_at")(_aware)
    _aware_valid_until = field_validator("valid_until")(_aware)

    @model_validator(mode="after")
    def outcome_consistency(self) -> "PolicyDecisionSpec":
        if self.valid_until is not None and self.valid_until <= self.issued_at:
            raise ValueError("valid_until must follow issued_at")
        if self.outcome == "deny":
            if not self.safe_reason or not self.reason_codes:
                raise ValueError("denial requires a safe reason and reason code")
            if self.effective_authority is not None or self.effective_budget is not None:
                raise ValueError("denial cannot grant authority or budget")
        elif self.effective_authority is None:
            raise ValueError("non-denial decisions require effective authority")
        if self.outcome == "require_approval" and self.approval_requirement is None:
            raise ValueError("approval outcome requires an approval requirement")
        if self.outcome != "require_approval" and self.approval_requirement is not None:
            raise ValueError("only approval outcomes may contain approval requirements")
        if self.outcome == "allow" and self.constraints:
            raise ValueError("unconditional allow cannot contain constraints")
        if self.outcome == "constrained_allow" and not self.constraints:
            raise ValueError("constrained allow requires constraints")
        return self


class PolicyDecision(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["PolicyDecision"]
    metadata: ResourceMetadata
    spec: PolicyDecisionSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}
