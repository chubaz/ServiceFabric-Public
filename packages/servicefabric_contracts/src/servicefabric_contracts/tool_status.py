"""Mutable observed operational state, separate from desired tool contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .common import ContractModel, Identifier, ToolIdentifier
from .metadata import ResourceMetadata
from .tool_deployment import ToolRevisionReference


class ToolCondition(ContractModel):
    type: Identifier
    status: Literal["true", "false", "unknown"]
    reason: Identifier
    message: str = Field(min_length=1, max_length=2000)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, observed_at: datetime) -> datetime:
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("condition timestamps must include a timezone")
        return observed_at


class ToolStatusSpec(ContractModel):
    tool_id: ToolIdentifier
    deployment_ref: Identifier
    revision_ref: ToolRevisionReference
    availability: Literal["unknown", "available", "degraded", "unavailable", "disabled"]
    maintenance_state: Literal["unknown", "normal", "maintenance", "quarantined"]
    readiness: Literal["unknown", "ready", "not_ready"]
    last_transition: datetime
    conditions: tuple[ToolCondition, ...] = Field(default_factory=tuple, max_length=64)
    observed_version: int = Field(ge=1)
    observed_evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=64)

    @field_validator("last_transition")
    @classmethod
    def require_transition_timezone(cls, transition: datetime) -> datetime:
        if transition.tzinfo is None or transition.utcoffset() is None:
            raise ValueError("last transition must include a timezone")
        return transition

    @field_validator("observed_evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, references: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(references)) != len(references) or any(not reference.startswith("evidence://") for reference in references):
            raise ValueError("observations must use unique opaque evidence references")
        return references

    @model_validator(mode="after")
    def revision_matches_tool(self) -> "ToolStatusSpec":
        if self.revision_ref.tool_id != self.tool_id:
            raise ValueError("status revision must belong to the observed tool")
        return self


class ToolStatus(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolStatus"]
    metadata: ResourceMetadata
    spec: ToolStatusSpec

    model_config = ContractModel.model_config | {"populate_by_name": True}
