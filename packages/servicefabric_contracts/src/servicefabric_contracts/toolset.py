"""Declarative portfolio grouping without routing or execution behavior."""
from typing import Literal
from pydantic import Field, field_validator
from .common import ContractModel, Identifier, ToolIdentifier
from .metadata import ResourceMetadata

class ToolsetMember(ContractModel):
    tool_id: ToolIdentifier
    revision_ref: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")

class ToolsetDefinitionSpec(ContractModel):
    toolset_id: Identifier
    description: str = Field(min_length=1, max_length=2000)
    members: tuple[ToolsetMember, ...] = Field(min_length=1, max_length=128)
    @field_validator("members")
    @classmethod
    def unique_members(cls, value):
        if len({x.tool_id for x in value}) != len(value): raise ValueError("toolset members must be unique")
        return tuple(sorted(value,key=lambda x:x.tool_id))

class ToolsetDefinition(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolsetDefinition"]
    metadata: ResourceMetadata
    spec: ToolsetDefinitionSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}
