"""Immutable executable contract revisions for stable tool definitions."""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .common import Digest, Identifier, ImmutableContractModel, SEMVER_PATTERN, ToolIdentifier
from .dependencies import DependencyContract
from .effects import EffectContract
from .execution_binding import ExecutionBinding
from .metadata import ResourceMetadata
from .reliability import CancellationDeclaration, IdempotencyDeclaration


class ToolDefinitionReference(ImmutableContractModel):
    tool_id: ToolIdentifier


class ServicePackageRevisionReference(ImmutableContractModel):
    package_id: Identifier
    package_version: str = Field(pattern=SEMVER_PATTERN)
    entrypoint_id: Identifier


class SchemaReference(ImmutableContractModel):
    schema_ref: str = Field(min_length=3, max_length=256, pattern=r"^schema://[a-z][a-z0-9._:/-]+$")
    schema_digest: Digest


class ErrorContractDeclaration(ImmutableContractModel):
    error_codes: tuple[Identifier, ...] = Field(min_length=1, max_length=64)
    categories: tuple[Literal["validation", "authorization", "approval", "policy", "dependency", "timeout", "cancelled", "rate_limit", "business_rule", "quality", "conflict", "unavailable", "internal"], ...]

    @field_validator("error_codes", "categories")
    @classmethod
    def unique_values(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("error contract values must be unique")
        return values


class RevisionResourceRequirements(ImmutableContractModel):
    cpu_millicores: int | None = Field(default=None, ge=1, le=64000)
    memory_mebibytes: int | None = Field(default=None, ge=16, le=1048576)
    network_policy_ref: str = Field(min_length=3, max_length=256, pattern=r"^policy://[a-z][a-z0-9._:/-]+$")
    storage_requirement_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=32)


class TimeoutDeclaration(ImmutableContractModel):
    timeout_class: Literal["short", "bounded_long", "durable"]
    maximum_timeout_ms: int = Field(ge=1, le=86400000)


class EvidencePolicy(ImmutableContractModel):
    evidence_required: bool
    evidence_policy_ref: str | None = Field(default=None, min_length=3, max_length=256, pattern=r"^policy://[a-z][a-z0-9._:/-]+$")

    @model_validator(mode="after")
    def validate_reference(self) -> "EvidencePolicy":
        if self.evidence_required != (self.evidence_policy_ref is not None):
            raise ValueError("evidence requirement and policy reference must agree")
        return self


class CompatibilityDeclaration(ImmutableContractModel):
    minimum_contract_version: str = Field(pattern=SEMVER_PATTERN)
    compatible_definition_revisions: tuple[str, ...] = Field(default_factory=tuple, max_length=32)


class RevisionProvenance(ImmutableContractModel):
    source_ref: str = Field(min_length=3, max_length=256, pattern=r"^source://[a-z][a-z0-9._:/-]+$")
    source_digest: Digest
    build_ref: str = Field(min_length=3, max_length=256, pattern=r"^build://[a-z][a-z0-9._:/-]+$")


class ToolRevisionSpec(ImmutableContractModel):
    tool_id: ToolIdentifier
    revision: str = Field(pattern=SEMVER_PATTERN)
    definition_ref: ToolDefinitionReference
    package_ref: ServicePackageRevisionReference
    execution_binding: ExecutionBinding
    input_schema: SchemaReference
    output_schema: SchemaReference
    error_contract: ErrorContractDeclaration
    effect_contract: EffectContract
    dependency_contract: DependencyContract
    resource_requirements: RevisionResourceRequirements
    timeouts: TimeoutDeclaration
    idempotency: IdempotencyDeclaration
    cancellation: CancellationDeclaration
    evidence_policy: EvidencePolicy
    compatibility: CompatibilityDeclaration
    provenance: RevisionProvenance
    content_digest: Digest

    @field_validator("revision")
    @classmethod
    def reject_mutable_revision_aliases(cls, revision: str) -> str:
        if revision.lower() in {"latest", "current", "active", "production"}:
            raise ValueError("revision identifiers must be immutable")
        return revision

    @model_validator(mode="after")
    def validate_revision_relationships(self) -> "ToolRevisionSpec":
        if self.tool_id != self.definition_ref.tool_id:
            raise ValueError("revision must reference exactly its ToolDefinition")
        binding_package = getattr(self.execution_binding, "service_package_id", None)
        binding_package = binding_package or getattr(self.execution_binding, "external_package_id", None)
        if binding_package and binding_package != self.package_ref.package_id:
            raise ValueError("execution binding package must match package_ref")
        if self.effect_contract.is_effectful and self.idempotency.idempotency_class == "unknown":
            raise ValueError("effectful revisions require explicit idempotency behavior")
        irreversible = any(effect.reversibility == "irreversible" for effect in self.effect_contract.effects)
        if irreversible and self.idempotency.retry_safety == "safe":
            raise ValueError("irreversible effects cannot declare unrestricted retry safety")
        return self

    def calculated_content_digest(self) -> str:
        payload = self.model_dump(mode="json", exclude={"content_digest"})
        content = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


class ToolRevision(ImmutableContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolRevision"]
    metadata: ResourceMetadata
    spec: ToolRevisionSpec

    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}
