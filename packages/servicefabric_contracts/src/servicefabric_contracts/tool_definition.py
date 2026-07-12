"""Stable semantic identity and desired behavior of one bounded operation."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .behavior import CapabilityDeclaration, ToolBehavior
from .common import ContractModel, Identifier, ToolIdentifier
from .effects import EffectContract
from .lifecycle import ToolLifecycleDeclaration
from .mcp_projection import McpProjection
from .metadata import ResourceMetadata
from .observability import ObservabilityDeclaration
from .permissions import PermissionContract
from .quality import QualityDeclaration
from .reliability import ReliabilityDeclaration


class ToolDefinitionSpec(ContractModel):
    tool_id: ToolIdentifier
    name: Identifier
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=4000)
    capability: CapabilityDeclaration
    behavior: ToolBehavior
    input_contract_ref: str = Field(min_length=3, max_length=256, pattern=r"^schema://[a-z][a-z0-9._:/-]+$")
    output_contract_ref: str = Field(min_length=3, max_length=256, pattern=r"^schema://[a-z][a-z0-9._:/-]+$")
    declared_effects: EffectContract
    required_permissions: PermissionContract = Field(default_factory=PermissionContract)
    approval_policy_ref: str | None = Field(default=None, min_length=3, max_length=256, pattern=r"^policy://[a-z][a-z0-9._:/-]+$")
    reliability: ReliabilityDeclaration
    observability: ObservabilityDeclaration
    quality: QualityDeclaration
    lifecycle: ToolLifecycleDeclaration
    mcp_projection: McpProjection = Field(default_factory=McpProjection)

    @model_validator(mode="after")
    def validate_behavior_and_effects(self) -> "ToolDefinitionSpec":
        if self.declared_effects.is_effectful == (self.behavior.side_effect_class == "none"):
            raise ValueError("behavior side-effect class must agree with declared effects")
        if any(effect.approval_required for effect in self.declared_effects.effects) and not self.approval_policy_ref:
            raise ValueError("approval-requiring effects need an approval policy reference")
        return self


class ToolDefinition(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolDefinition"]
    metadata: ResourceMetadata
    spec: ToolDefinitionSpec

    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def metadata_matches_tool_identity(self) -> "ToolDefinition":
        if self.metadata.id != self.spec.tool_id:
            raise ValueError("metadata id must match the stable tool_id")
        return self
