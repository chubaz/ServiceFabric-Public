"""Canonical immutable-application and build-boundary contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .budgets import ExecutionBudget
from .caller import CallerContext
from .common import ContractModel, Digest, Identifier, ImmutableContractModel, SEMVER_PATTERN
from .errors import ToolError
from .evidence import EvidenceRecord
from .metadata import ResourceMetadata
from .warnings import ToolWarning


def _safe_relative_path(value: str) -> str:
    value = value.replace("\\", "/")
    parts = value.split("/")
    if not value or value.startswith("/") or "\x00" in value or ":" in parts[0]:
        raise ValueError("path must be a bounded relative POSIX path")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("path traversal and empty path segments are forbidden")
    if len(value) > 512 or any(len(part) > 128 for part in parts):
        raise ValueError("path exceeds bounded length")
    return value


class StaticWebBuildSpec(ImmutableContractModel):
    build_type: Literal["static_web"] = "static_web"
    entry_document: str
    include_patterns: tuple[str, ...] = ("**/*",)
    exclude_patterns: tuple[str, ...] = ()
    maximum_file_count: int = Field(default=256, ge=1, le=4096)
    maximum_source_bytes: int = Field(default=16_777_216, ge=1, le=134_217_728)
    maximum_output_bytes: int = Field(default=16_777_216, ge=1, le=134_217_728)
    normalization_policy: Literal["utf8_lf_final_newline"] = "utf8_lf_final_newline"

    _entry_path = field_validator("entry_document")(_safe_relative_path)

    @field_validator("include_patterns", "exclude_patterns")
    @classmethod
    def safe_patterns(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) > 32 or len(set(values)) != len(values):
            raise ValueError("patterns must be unique and bounded")
        for value in values:
            if not value or value.startswith(("/", "~")) or ".." in value or "\\" in value:
                raise ValueError("patterns must be relative and cannot traverse")
        return values


class SourceFileManifest(ImmutableContractModel):
    path: str
    content_digest: Digest
    media_type: str = Field(min_length=3, max_length=128, pattern=r"^[a-z0-9.+-]+/[a-z0-9.+-]+$")
    size_bytes: int = Field(ge=0, le=134_217_728)
    executable: Literal[False] = False

    _path = field_validator("path")(_safe_relative_path)


class SourceBundleManifest(ImmutableContractModel):
    source_digest: Digest
    files: tuple[SourceFileManifest, ...] = Field(min_length=1, max_length=4096)
    total_size_bytes: int = Field(ge=0, le=134_217_728)

    @model_validator(mode="after")
    def validate_files(self) -> "SourceBundleManifest":
        paths = [item.path for item in self.files]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("source files must have unique deterministic path ordering")
        if sum(item.size_bytes for item in self.files) != self.total_size_bytes:
            raise ValueError("source total does not match file sizes")
        return self


class ApplicationDefinitionSpec(ContractModel):
    application_id: Identifier
    display_name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=4000)
    application_type: Literal["static_web"]
    status: Literal["draft", "reviewed", "deprecated"] = "draft"
    labels: dict[str, str] = Field(default_factory=dict, max_length=64)
    annotations: dict[str, str] = Field(default_factory=dict, max_length=64)


class ApplicationDefinition(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApplicationDefinition"]
    metadata: ResourceMetadata
    spec: ApplicationDefinitionSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def identity_matches(self) -> "ApplicationDefinition":
        if self.metadata.id != self.spec.application_id:
            raise ValueError("metadata ID must equal application ID")
        return self


class ApplicationRevisionSpec(ImmutableContractModel):
    application_id: Identifier
    revision: str = Field(pattern=SEMVER_PATTERN)
    application_type: Literal["static_web"]
    source_bundle_ref: Identifier
    source_digest: Digest
    build_spec: StaticWebBuildSpec
    output_format: Literal["directory"] = "directory"
    created_from: Digest
    status: Literal["reviewed"] = "reviewed"


class ApplicationRevision(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApplicationRevision"]
    metadata: ResourceMetadata
    spec: ApplicationRevisionSpec
    model_config = ContractModel.model_config | {"populate_by_name": True, "frozen": True}


class ApplicationBuildRequestSpec(ContractModel):
    request_id: Identifier
    application_id: Identifier
    revision: str = Field(pattern=SEMVER_PATTERN)
    requested_artifact_format: Literal["directory"] = "directory"
    caller_context: CallerContext
    execution_budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    correlation_ref: Identifier | None = None


class ApplicationBuildRequest(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApplicationBuildRequest"]
    metadata: ResourceMetadata
    spec: ApplicationBuildRequestSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}


class ArtifactFileManifest(ImmutableContractModel):
    path: str
    content_digest: Digest
    media_type: str = Field(min_length=3, max_length=128)
    size_bytes: int = Field(ge=0)
    _path = field_validator("path")(_safe_relative_path)


class ArtifactProvenance(ImmutableContractModel):
    source_manifest_ref: Identifier
    source_digest: Digest
    build_spec_digest: Digest
    builder_id: Identifier
    builder_revision: str = Field(pattern=SEMVER_PATTERN)


class ApplicationArtifactManifestSpec(ImmutableContractModel):
    artifact_id: Identifier
    artifact_digest: Digest
    application_id: Identifier
    application_revision: str = Field(pattern=SEMVER_PATTERN)
    builder_id: Identifier
    builder_revision: str = Field(pattern=SEMVER_PATTERN)
    source_digest: Digest
    build_spec_digest: Digest
    files: tuple[ArtifactFileManifest, ...] = Field(min_length=1, max_length=4096)
    entry_document: str
    total_size_bytes: int = Field(ge=0)
    created_at: datetime | None = None
    reproducibility: Literal["reproducible", "conditionally_reproducible", "not_reproducible"]
    provenance: ArtifactProvenance
    _entry_path = field_validator("entry_document")(_safe_relative_path)

    @field_validator("created_at")
    @classmethod
    def aware_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("created_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_content(self) -> "ApplicationArtifactManifestSpec":
        paths = [item.path for item in self.files]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("artifact files must have unique deterministic path ordering")
        if self.entry_document not in paths:
            raise ValueError("entry document must exist in artifact files")
        if sum(item.size_bytes for item in self.files) != self.total_size_bytes:
            raise ValueError("artifact total does not match file sizes")
        return self


class ApplicationArtifactManifest(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApplicationArtifactManifest"]
    metadata: ResourceMetadata
    spec: ApplicationArtifactManifestSpec
    model_config = ContractModel.model_config | {"populate_by_name": True, "frozen": True}


class ApplicationBuildResult(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ApplicationBuildResult"]
    status: Literal["success", "error"]
    application_id: Identifier
    revision: str = Field(pattern=SEMVER_PATTERN)
    build_id: Identifier
    artifact_ref: Identifier | None = None
    artifact_digest: Digest | None = None
    artifact_manifest_ref: Identifier | None = None
    warnings: tuple[ToolWarning, ...] = ()
    errors: tuple[ToolError, ...] = ()
    evidence: tuple[EvidenceRecord, ...] = ()
    metrics: dict[str, int] = Field(default_factory=dict, max_length=32)
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def result_consistency(self) -> "ApplicationBuildResult":
        artifact_fields = (self.artifact_ref, self.artifact_digest, self.artifact_manifest_ref)
        if self.status == "success" and (not all(artifact_fields) or self.errors):
            raise ValueError("successful builds require complete artifact identity and no errors")
        if self.status == "error" and (not self.errors or any(artifact_fields)):
            raise ValueError("failed builds require errors and cannot claim an artifact")
        return self
