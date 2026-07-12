"""Immutable durable-operation history, attempt, and reconciliation records."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .common import Digest, Identifier, ImmutableContractModel
from .errors import ToolError
from .metadata import ResourceMetadata
from .observed_effects import ObservedEffect


OperationState = Literal[
    "accepted", "queued", "running", "waiting_for_approval", "waiting_for_dependency",
    "waiting_for_human", "succeeded", "partially_succeeded", "failed", "cancelled", "timed_out",
]


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return value
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


class OperationTransitionSpec(ImmutableContractModel):
    transition_id: Identifier
    operation_ref: Identifier
    from_state: OperationState
    to_state: OperationState
    expected_version: int = Field(ge=1)
    resulting_version: int = Field(ge=2)
    reason_code: Identifier
    safe_reason: str = Field(min_length=1, max_length=1000)
    transitioned_at: datetime
    actor_ref: Identifier
    approval_binding_ref: Identifier | None = None
    attempt_ref: Identifier | None = None
    result_ref: Identifier | None = None
    error: ToolError | None = None
    evidence_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)

    _aware_transitioned_at = field_validator("transitioned_at")(_aware)

    @model_validator(mode="after")
    def version_consistency(self) -> "OperationTransitionSpec":
        if self.resulting_version != self.expected_version + 1:
            raise ValueError("transition must increment operation version exactly once")
        if self.from_state == self.to_state:
            raise ValueError("operation transition cannot retain the same state")
        if self.to_state == "failed" and self.error is None:
            raise ValueError("failed transition requires a ToolError")
        if self.to_state == "succeeded" and self.error is not None:
            raise ValueError("successful transition cannot contain an error")
        return self


class OperationTransition(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["OperationTransition"]
    metadata: ResourceMetadata
    spec: OperationTransitionSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}


class OperationEventDetail(ImmutableContractModel):
    key: Identifier
    value: str = Field(min_length=1, max_length=512)


class OperationEventSpec(ImmutableContractModel):
    event_id: Identifier
    operation_ref: Identifier
    sequence: int = Field(ge=1)
    operation_version: int = Field(ge=1)
    event_type: Literal["accepted", "transition", "attempt", "approval", "cancellation", "reconciliation", "evidence"]
    recorded_at: datetime
    previous_event_digest: Digest | None = None
    event_digest: Digest
    transition_ref: Identifier | None = None
    attempt_ref: Identifier | None = None
    approval_ref: Identifier | None = None
    evidence_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    details: tuple[OperationEventDetail, ...] = Field(default_factory=tuple, max_length=32)

    _aware_recorded_at = field_validator("recorded_at")(_aware)

    @model_validator(mode="after")
    def chain_consistency(self) -> "OperationEventSpec":
        if self.sequence == 1 and self.previous_event_digest is not None:
            raise ValueError("first event cannot have a previous digest")
        if self.sequence > 1 and self.previous_event_digest is None:
            raise ValueError("subsequent events require a previous digest")
        if self.operation_version != self.sequence:
            raise ValueError("event sequence and operation version must match")
        return self


class OperationEvent(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["OperationEvent"]
    metadata: ResourceMetadata
    spec: OperationEventSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}


class IdempotencyRecordSpec(ImmutableContractModel):
    record_id: Identifier
    key_digest: Digest
    intent_digest: Digest
    scope: Literal["caller", "tenant", "deployment", "tool"]
    caller_ref: Identifier
    namespace_ref: Identifier | None = None
    request_ref: Identifier
    operation_ref: Identifier
    state: Literal["reserved", "in_progress", "completed", "failed", "expired"]
    created_at: datetime
    expires_at: datetime
    completed_result_ref: Identifier | None = None

    _aware_created_at = field_validator("created_at")(_aware)
    _aware_expires_at = field_validator("expires_at")(_aware)

    @model_validator(mode="after")
    def consistency(self) -> "IdempotencyRecordSpec":
        if self.expires_at <= self.created_at:
            raise ValueError("idempotency retention must be positive")
        if self.state == "completed" and self.completed_result_ref is None:
            raise ValueError("completed idempotency records require a result reference")
        if self.state != "completed" and self.completed_result_ref is not None:
            raise ValueError("only completed idempotency records may reference a result")
        return self

    def matches_intent(self, digest: str) -> bool:
        return digest == self.intent_digest


class IdempotencyRecord(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["IdempotencyRecord"]
    metadata: ResourceMetadata
    spec: IdempotencyRecordSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}


class ExecutionAttemptSpec(ImmutableContractModel):
    attempt_id: Identifier
    operation_ref: Identifier
    invocation_ref: Identifier
    revision_ref: str = Field(min_length=1, max_length=160)
    attempt_number: int = Field(ge=1, le=32)
    state: Literal["started", "succeeded", "failed", "cancelled", "timed_out", "uncertain"]
    started_at: datetime
    completed_at: datetime | None = None
    retry_eligibility: Literal["not_evaluated", "eligible", "ineligible", "blocked_pending_reconciliation"]
    next_eligible_at: datetime | None = None
    error: ToolError | None = None
    result_ref: Identifier | None = None
    evidence_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    effect_uncertainty: Literal["none", "possible", "confirmed"] = "none"

    _aware_started_at = field_validator("started_at")(_aware)
    _aware_completed_at = field_validator("completed_at")(_aware)
    _aware_next_eligible_at = field_validator("next_eligible_at")(_aware)

    @model_validator(mode="after")
    def consistency(self) -> "ExecutionAttemptSpec":
        terminal = self.state != "started"
        if terminal != (self.completed_at is not None):
            raise ValueError("terminal attempts require completed_at")
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("attempt completion cannot precede start")
        if self.state == "failed" and self.error is None:
            raise ValueError("failed attempts require an error")
        if self.state == "succeeded" and self.result_ref is None:
            raise ValueError("successful attempts require a result reference")
        if self.effect_uncertainty == "possible" and self.retry_eligibility != "blocked_pending_reconciliation":
            raise ValueError("possible effects must block retry pending reconciliation")
        return self


class ExecutionAttempt(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ExecutionAttempt"]
    metadata: ResourceMetadata
    spec: ExecutionAttemptSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}


class ReconciliationRecordSpec(ImmutableContractModel):
    reconciliation_id: Identifier
    operation_ref: Identifier
    attempt_ref: Identifier
    declared_effect_ref: Identifier
    observed_effect: ObservedEffect | None = None
    provider_operation_ref: Identifier | None = None
    idempotency_digest: Digest | None = None
    outcome: Literal["known_committed", "known_absent", "unknown", "verification_unavailable"]
    verification_method: Identifier | None = None
    verified_at: datetime
    effect_receipt_ref: Identifier | None = None
    evidence_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    error: ToolError | None = None
    safe_reason: str = Field(min_length=1, max_length=1000)

    _aware_verified_at = field_validator("verified_at")(_aware)

    @model_validator(mode="after")
    def consistency(self) -> "ReconciliationRecordSpec":
        if self.outcome == "known_committed":
            if self.observed_effect is None or self.effect_receipt_ref is None or self.verification_method is None:
                raise ValueError("known committed effects require observation, receipt, and verification method")
        if self.outcome == "known_absent" and self.verification_method is None:
            raise ValueError("known absent effects require a verification method")
        if self.outcome == "verification_unavailable" and self.error is None:
            raise ValueError("unavailable verification requires a safe error")
        if self.outcome in {"unknown", "verification_unavailable"} and self.effect_receipt_ref is not None:
            raise ValueError("unresolved reconciliation cannot claim an effect receipt")
        return self


class ReconciliationRecord(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ReconciliationRecord"]
    metadata: ResourceMetadata
    spec: ReconciliationRecordSpec
    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}
