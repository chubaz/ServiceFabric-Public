"""Verified caller identity declarations crossing the invocation boundary."""
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .common import ContractModel, Identifier

class CallerContext(ContractModel):
    subject_ref: Identifier
    principal_type: Literal["human", "service", "agent", "graph", "system", "anonymous"]
    tenant_ref: Identifier | None = None
    issuer: Identifier
    audiences: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=16)
    scopes: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    delegation_ref: Identifier | None = None
    authority_chain_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=16)
    authentication_strength: Literal["none", "single_factor", "multi_factor", "workload", "federated"]

    @field_validator("audiences", "scopes", "authority_chain_refs")
    @classmethod
    def unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values): raise ValueError("references must be unique")
        return values

    @model_validator(mode="after")
    def anonymous_has_no_authority(self):
        if self.principal_type == "anonymous" and (self.scopes or self.authentication_strength != "none"):
            raise ValueError("anonymous callers cannot carry authenticated authority")
        return self
