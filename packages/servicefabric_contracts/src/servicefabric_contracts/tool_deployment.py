"""Desired deployment and routing declarations for immutable tool revisions."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, field_validator, model_validator

from .common import ContractModel, Digest, Identifier, SEMVER_PATTERN, ToolIdentifier
from .metadata import ResourceMetadata


class ToolRevisionReference(ContractModel):
    tool_id: ToolIdentifier
    revision: str = Field(pattern=SEMVER_PATTERN)
    content_digest: Digest


class SingleTrafficPolicy(ContractModel):
    traffic_kind: Literal["single"]


class WeightedTrafficTarget(ContractModel):
    revision_ref: ToolRevisionReference
    percentage: int = Field(ge=1, le=100)


class WeightedTrafficPolicy(ContractModel):
    traffic_kind: Literal["weighted"]
    targets: tuple[WeightedTrafficTarget, ...] = Field(min_length=2, max_length=16)

    @field_validator("targets")
    @classmethod
    def validate_total(cls, targets: tuple[WeightedTrafficTarget, ...]) -> tuple[WeightedTrafficTarget, ...]:
        if sum(target.percentage for target in targets) != 100:
            raise ValueError("weighted traffic must total exactly 100 percent")
        revisions = [(target.revision_ref.tool_id, target.revision_ref.revision) for target in targets]
        if len(set(revisions)) != len(revisions):
            raise ValueError("weighted traffic revisions must be unique")
        return targets


class ShadowTrafficPolicy(ContractModel):
    traffic_kind: Literal["shadow"]
    shadow_revision_ref: ToolRevisionReference
    shadow_percentage: int = Field(ge=1, le=100)


class DisabledTrafficPolicy(ContractModel):
    traffic_kind: Literal["disabled"]


TrafficPolicy = Annotated[
    Union[SingleTrafficPolicy, WeightedTrafficPolicy, ShadowTrafficPolicy, DisabledTrafficPolicy],
    Field(discriminator="traffic_kind"),
]


class ActivationPolicy(ContractModel):
    mode: Literal["immediate", "manual", "scheduled", "disabled"]
    schedule_ref: str | None = Field(default=None, min_length=3, max_length=256, pattern=r"^schedule://[a-z][a-z0-9._:/-]+$")

    @model_validator(mode="after")
    def validate_schedule(self) -> "ActivationPolicy":
        if (self.mode == "scheduled") != (self.schedule_ref is not None):
            raise ValueError("scheduled activation requires exactly one schedule reference")
        return self


class DeploymentProvenance(ContractModel):
    change_ref: str = Field(min_length=3, max_length=256, pattern=r"^change://[a-z][a-z0-9._:/-]+$")
    actor_ref: Identifier


class ToolDeploymentSpec(ContractModel):
    deployment_id: Identifier
    tool_id: ToolIdentifier
    revision_ref: ToolRevisionReference
    environment: Identifier
    execution_target_ref: str = Field(min_length=3, max_length=256, pattern=r"^target://[a-z][a-z0-9._:/-]+$")
    traffic_policy: TrafficPolicy
    activation_policy: ActivationPolicy
    tenant_scope: Literal["single_tenant", "multi_tenant", "platform"]
    policy_set_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    configuration_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    credential_binding_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    created_provenance: DeploymentProvenance

    @field_validator("policy_set_refs")
    @classmethod
    def validate_policy_refs(cls, references: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(references)) != len(references) or any(not reference.startswith("policy://") for reference in references):
            raise ValueError("policy sets must be unique opaque policy references")
        return references

    @field_validator("configuration_refs")
    @classmethod
    def validate_configuration_refs(cls, references: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(references)) != len(references) or any(not reference.startswith("config://") for reference in references):
            raise ValueError("configurations must be unique opaque config references")
        return references

    @field_validator("credential_binding_refs")
    @classmethod
    def validate_credential_binding_refs(cls, references: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(references)) != len(references):
            raise ValueError("credential binding references must be unique")
        return references

    @model_validator(mode="after")
    def validate_revision_relationships(self) -> "ToolDeploymentSpec":
        if self.tool_id != self.revision_ref.tool_id:
            raise ValueError("deployment tool_id must match its immutable revision reference")
        if isinstance(self.traffic_policy, WeightedTrafficPolicy):
            if not any(target.revision_ref == self.revision_ref for target in self.traffic_policy.targets):
                raise ValueError("weighted traffic must include the deployment revision_ref")
        if isinstance(self.traffic_policy, ShadowTrafficPolicy) and self.traffic_policy.shadow_revision_ref == self.revision_ref:
            raise ValueError("shadow revision must differ from the primary revision")
        return self


class ToolDeployment(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolDeployment"]
    metadata: ResourceMetadata
    spec: ToolDeploymentSpec

    model_config = ContractModel.model_config | {"populate_by_name": True}
