"""Declarative timeout, retry, cancellation, and idempotency requirements."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .common import ImmutableContractModel


class ReliabilityDeclaration(ImmutableContractModel):
    availability_class: Literal["best_effort", "standard", "critical"]
    timeout_class: Literal["short", "bounded_long", "durable"]
    maximum_timeout_ms: int = Field(ge=1, le=86400000)
    retry_policy: Literal["none", "bounded", "policy_controlled"]


class IdempotencyDeclaration(ImmutableContractModel):
    idempotency_class: Literal["naturally_idempotent", "keyed_idempotent", "non_idempotent", "unknown"]
    idempotency_key_supported: bool
    retry_safety: Literal["safe", "unsafe", "conditional"]
    duplicate_delivery_behavior: Literal["deduplicate", "return_previous", "reject", "compensate", "manual_review"]

    @model_validator(mode="after")
    def validate_key_support(self) -> "IdempotencyDeclaration":
        if self.idempotency_class == "keyed_idempotent" and not self.idempotency_key_supported:
            raise ValueError("keyed idempotency requires idempotency-key support")
        return self


class CancellationDeclaration(ImmutableContractModel):
    supported: bool
    behavior: Literal["not_supported", "best_effort", "cooperative", "durable_checkpoint"]

    @model_validator(mode="after")
    def validate_behavior(self) -> "CancellationDeclaration":
        if self.supported == (self.behavior == "not_supported"):
            raise ValueError("cancellation support and behavior are inconsistent")
        return self
