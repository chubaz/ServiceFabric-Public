"""The v1alpha1 ServicePackageDefinition desired-state resource."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from .artifacts import (
    ArtifactReference,
    ExternalMcpArtifact,
    ExternalServiceArtifact,
    GraphRevisionArtifact,
    NoArtifact,
    OciImageArtifact,
    ProcessBundleArtifact,
    StaticBundleArtifact,
)
from .common import ContractModel, Identifier, SEMVER_PATTERN
from .entrypoints import EntrypointDeclaration
from .hosting import HostingDeclaration
from .metadata import OwnerReference, ResourceMetadata
from .runtime_requirements import HealthDeclaration, NetworkPolicy, RuntimeRequirements, StorageRequirement


class OwnershipDeclaration(ContractModel):
    owner_ref: OwnerReference
    support_ref: OwnerReference | None = None


class LifecycleDeclaration(ContractModel):
    maturity: Literal["experimental", "alpha", "beta", "stable", "deprecated"] = "experimental"
    deprecation_status: Literal["active", "deprecated", "retired"] = "active"
    replacement_ref: Identifier | None = None
    support_status: Literal["supported", "best_effort", "unsupported"] = "best_effort"

    @model_validator(mode="after")
    def validate_replacement(self) -> "LifecycleDeclaration":
        if self.deprecation_status == "deprecated" and not self.replacement_ref:
            raise ValueError("deprecated packages require a replacement reference")
        if self.deprecation_status != "deprecated" and self.replacement_ref:
            raise ValueError("replacement reference is only valid for deprecated packages")
        return self


class ServicePackageSpec(ContractModel):
    package_version: str = Field(pattern=SEMVER_PATTERN)
    description: str = Field(min_length=1, max_length=4000)
    hosting: HostingDeclaration
    artifact: ArtifactReference
    entrypoints: list[EntrypointDeclaration] = Field(default_factory=list, max_length=64)
    declared_capabilities: list[Identifier] = Field(default_factory=list, max_length=128)
    runtime_requirements: RuntimeRequirements = Field(default_factory=RuntimeRequirements)
    network_policy: NetworkPolicy = Field(default_factory=NetworkPolicy)
    storage_requirements: list[StorageRequirement] = Field(default_factory=list, max_length=32)
    health: HealthDeclaration
    ownership: OwnershipDeclaration
    lifecycle: LifecycleDeclaration = Field(default_factory=LifecycleDeclaration)

    @field_validator("entrypoints")
    @classmethod
    def unique_entrypoint_ids(cls, entrypoints: list[EntrypointDeclaration]) -> list[EntrypointDeclaration]:
        identifiers = [entrypoint.id for entrypoint in entrypoints]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("entrypoint IDs must be unique inside a package")
        return entrypoints

    @field_validator("declared_capabilities")
    @classmethod
    def unique_capabilities(cls, capabilities: list[str]) -> list[str]:
        if len(set(capabilities)) != len(capabilities):
            raise ValueError("declared capabilities must be unique")
        return capabilities

    @model_validator(mode="after")
    def validate_hosting_and_artifact(self) -> "ServicePackageSpec":
        expected = {
            "managed_container": OciImageArtifact,
            "managed_static": StaticBundleArtifact,
            "managed_process": ProcessBundleArtifact,
            "managed_graph": GraphRevisionArtifact,
            "external_service": ExternalServiceArtifact,
            "external_mcp": ExternalMcpArtifact,
            "none": NoArtifact,
        }[self.hosting.mode]
        if not isinstance(self.artifact, expected):
            raise ValueError(f"{self.hosting.mode} requires a matching {expected.__name__} artifact")
        if not self.entrypoints and self.hosting.mode != "none":
            raise ValueError("packages without entrypoints must use none hosting")
        if self.hosting.mode in {"external_service", "external_mcp", "none"} and self.hosting.managed_resources:
            raise ValueError("external and none hosting cannot declare managed resources")
        if self.hosting.mode == "none" and (self.storage_requirements or self.runtime_requirements.compute):
            raise ValueError("none hosting cannot declare managed runtime resources")
        for entrypoint in self.entrypoints:
            has_mcp = any(exposure.kind == "mcp" for exposure in entrypoint.exposures)
            if has_mcp and entrypoint.kind == "cli" and not entrypoint.machine_callable:
                raise ValueError("CLI MCP exposure requires a machine-callable entrypoint")
        return self


class ServicePackageDefinition(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ServicePackageDefinition"]
    metadata: ResourceMetadata
    spec: ServicePackageSpec

    model_config = ContractModel.model_config | {"populate_by_name": True}
