from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .common import ContractModel, Digest, Identifier, ToolIdentifier
from .metadata import ResourceMetadata
from .observed_effects import ObservedEffect
class EffectReceiptSpec(ContractModel):
    receipt_id: Identifier
    invocation_id: Identifier
    tool_id: ToolIdentifier
    revision_ref: str = Field(pattern=r"^[a-z0-9][a-z0-9._:-]+$")
    declared_effect_ref: Identifier
    observed_effects: tuple[ObservedEffect, ...] = Field(default_factory=tuple, max_length=64)
    verification_status: Literal["unverified", "verified", "partially_verified", "verification_failed", "reconciled"]
    verification_method: Identifier | None = None
    verified_no_op: bool = False
    idempotency_digest: Digest | None = None
    issued_at: datetime
    evidence_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    @field_validator("revision_ref")
    @classmethod
    def immutable_revision(cls, value):
        if value in {"latest", "current", "production"}: raise ValueError("revision aliases are not immutable")
        return value
    @model_validator(mode="after")
    def verification_consistency(self):
        if self.verification_status in {"verified", "partially_verified", "reconciled"}:
            if not self.verification_method: raise ValueError("verified receipts require a verification method")
            if not self.observed_effects and not self.verified_no_op: raise ValueError("verified receipts require an observed effect or verified no-op")
        return self
class EffectReceipt(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["EffectReceipt"]
    metadata: ResourceMetadata
    spec: EffectReceiptSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}
