"""Typed unresolved dependency references for immutable tool revisions."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, field_validator

from .common import Identifier, ImmutableContractModel, ToolIdentifier


class ToolDependency(ImmutableContractModel):
    dependency_kind: Literal["tool"]
    tool_id: ToolIdentifier
    revision_constraint: str = Field(min_length=1, max_length=64)


class ProviderDependency(ImmutableContractModel):
    dependency_kind: Literal["provider"]
    provider_ref: Identifier


class ExternalServiceDependency(ImmutableContractModel):
    dependency_kind: Literal["external_service"]
    service_ref: Identifier


class DataDependency(ImmutableContractModel):
    dependency_kind: Literal["data"]
    data_ref: str = Field(min_length=3, max_length=256, pattern=r"^data://[a-z][a-z0-9._:/-]+$")


class CredentialBindingDependency(ImmutableContractModel):
    dependency_kind: Literal["credential_binding"]
    credential_binding_ref: Identifier
    purpose: str = Field(min_length=1, max_length=160)


class GraphDependency(ImmutableContractModel):
    dependency_kind: Literal["graph"]
    graph_revision_ref: str = Field(min_length=3, max_length=256, pattern=r"^graph://[a-z][a-z0-9._:/-]+$")


class HumanDependency(ImmutableContractModel):
    dependency_kind: Literal["human"]
    workflow_ref: Identifier


DependencyDeclaration = Annotated[
    Union[
        ToolDependency,
        ProviderDependency,
        ExternalServiceDependency,
        DataDependency,
        CredentialBindingDependency,
        GraphDependency,
        HumanDependency,
    ],
    Field(discriminator="dependency_kind"),
]


class DependencyContract(ImmutableContractModel):
    dependencies: tuple[DependencyDeclaration, ...] = Field(default_factory=tuple, max_length=64)

    @field_validator("dependencies")
    @classmethod
    def reject_duplicate_dependencies(cls, dependencies: tuple[DependencyDeclaration, ...]) -> tuple[DependencyDeclaration, ...]:
        serialized = [dependency.model_dump_json() for dependency in dependencies]
        if len(set(serialized)) != len(serialized):
            raise ValueError("dependency declarations must be unique")
        return dependencies
