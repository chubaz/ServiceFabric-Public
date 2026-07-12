"""Immutable approval requests, decisions, and exact-intent bindings."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .common import Digest, Identifier, ImmutableContractModel, ToolIdentifier
from .governance import AuthorityGrant, RiskClass
from .metadata import ResourceMetadata


ApprovalOutcome = Literal["approved", "denied", "expired", "revoked"]


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return value
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


class ApprovalScope(ImmutableContractModel):
    effect_refs: tuple[Identifier, ...] = Field(min_length=1, max_length=32)
    authority: AuthorityGrant
    single_use: bool = True


class ApprovalRequestSpec(ImmutableContractModel):
    approval_request_id: Identifier
    policy_decision_ref: Identifier
    policy_decision_digest: Digest
    request_ref: Identifier
    operation_ref: Identifier
    caller_ref: Identifier
    tenant_ref: Identifier | None = None
    tool_id: ToolIdentifier
    revision_ref: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9][a-z0-9._:-]+$")
    intent_digest: Digest
    argument_digest: Digest
    effect_class: Identifier
    requested_authority: AuthorityGrant
    approval_scope: ApprovalScope
    risk: RiskClass
    reason: str = Field(min_length=1, max_length=1000)
    created_at: datetime
    expires_at: datetime

    _aware_created_at = field_validator("created_at")(_aware)
    _aware_expires_at = field_validator("expires_at")(_aware)

    @model_validator(mode="after")
    def consistency(self) -> "ApprovalRequestSpec":
        if self.expires_at <= self.created_at:
            raise ValueError("approval request expiry must follow creation")
        if self.effect_class not in self.approval_scope.effect_refs:
            raise ValueError("effect class must be included in approval scope")
        return self


class ApprovalRequest(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApprovalRequest"]
    metadata: ResourceMetadata
    spec: ApprovalRequestSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}


class ApprovalDecisionSpec(ImmutableContractModel):
    approval_decision_id: Identifier
    approval_request_ref: Identifier
    approval_request_digest: Digest
    policy_decision_ref: Identifier
    intent_digest: Digest
    outcome: ApprovalOutcome
    approver_subject_ref: Identifier
    approver_authority_ref: Identifier
    decided_at: datetime
    valid_until: datetime | None = None
    supersedes_decision_ref: Identifier | None = None
    reason_code: Identifier
    safe_reason: str = Field(min_length=1, max_length=1000)
    evidence_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)

    _aware_decided_at = field_validator("decided_at")(_aware)
    _aware_valid_until = field_validator("valid_until")(_aware)

    @model_validator(mode="after")
    def consistency(self) -> "ApprovalDecisionSpec":
        if self.valid_until is not None and self.valid_until <= self.decided_at:
            raise ValueError("approval validity must follow decision time")
        if self.outcome == "approved" and self.valid_until is None:
            raise ValueError("approved decisions require a validity limit")
        if self.outcome in {"revoked", "expired"} and self.supersedes_decision_ref is None:
            raise ValueError("revocation and expiration require a prior decision reference")
        if self.outcome in {"denied", "revoked", "expired"} and not self.safe_reason:
            raise ValueError("non-approved decisions require a safe reason")
        return self


class ApprovalDecision(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApprovalDecision"]
    metadata: ResourceMetadata
    spec: ApprovalDecisionSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}


class ApprovalBindingSpec(ImmutableContractModel):
    binding_id: Identifier
    approval_request_ref: Identifier
    approval_decision_ref: Identifier
    approval_decision_digest: Digest
    policy_decision_ref: Identifier
    policy_version: str = Field(min_length=1, max_length=64)
    caller_ref: Identifier
    tenant_ref: Identifier | None = None
    operation_ref: Identifier
    tool_id: ToolIdentifier
    revision_ref: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9][a-z0-9._:-]+$")
    intent_digest: Digest
    argument_digest: Digest
    effect_class: Identifier
    authority_scope: ApprovalScope
    valid_from: datetime
    valid_until: datetime
    binding_digest: Digest

    _aware_valid_from = field_validator("valid_from")(_aware)
    _aware_valid_until = field_validator("valid_until")(_aware)

    @model_validator(mode="after")
    def consistency(self) -> "ApprovalBindingSpec":
        if self.valid_until <= self.valid_from:
            raise ValueError("approval binding validity is empty")
        if self.effect_class not in self.authority_scope.effect_refs:
            raise ValueError("bound effect must be present in authority scope")
        return self

    def matches_intent(self, *, caller_ref: str, revision_ref: str, intent_digest: str, argument_digest: str) -> bool:
        return (
            caller_ref == self.caller_ref
            and revision_ref == self.revision_ref
            and intent_digest == self.intent_digest
            and argument_digest == self.argument_digest
        )


class ApprovalBinding(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApprovalBinding"]
    metadata: ResourceMetadata
    spec: ApprovalBindingSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}
