"""Canonical capsule hosting and authoring contracts."""

from __future__ import annotations

import json
import posixpath
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .budgets import ExecutionBudget
from .caller import CallerContext
from .common import ContractModel, Digest, Identifier, ImmutableContractModel, has_secret_like_key, is_json_value
from .effect_receipt import EffectReceipt
from .errors import ToolError
from .evidence import EvidenceRecord
from .metadata import OwnerReference, ResourceMetadata
from .warnings import ToolWarning


CAPSULE_TYPE = Literal["static_capsule"]
CAPSULE_STATUS = Literal["draft", "reviewed", "deprecated"]


def _canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _safe_identifier_path(value: str) -> str:
    if not value or "\x00" in value or "\\" in value or value.startswith("/") or ":" in value:
        raise ValueError("path must be a bounded relative path")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("path traversal is forbidden")
    if len(value) > 512 or any(len(part) > 128 for part in value.split("/")):
        raise ValueError("path exceeds bounded length")
    return value


def _normalize_route_path(value: str) -> str:
    if not value or "\x00" in value or "\\" in value or "?" in value or "#" in value or "%" in value:
        raise ValueError("route path must be explicit and unencoded")
    if not value.startswith("/"):
        raise ValueError("route path must be absolute")
    normalized = posixpath.normpath(value)
    if not normalized.startswith("/"):
        raise ValueError("route path normalization failed")
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    if normalized == "/":
        return normalized
    parts = normalized.split("/")[1:]
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("route path traversal is forbidden")
    if len(normalized) > 512:
        raise ValueError("route path exceeds bounded length")
    return normalized


def _route_path_key(value: str) -> tuple[int, str]:
    return (len(value), value)


class CapsuleArtifactBinding(ImmutableContractModel):
    binding_id: Identifier
    application_id: Identifier
    application_revision: str = Field(pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
    artifact_manifest_ref: Identifier
    artifact_digest: Digest
    mount_path: str
    entry_document: str
    required: bool = True

    _mount_path = field_validator("mount_path")(_normalize_route_path)
    _entry_document = field_validator("entry_document")(_safe_identifier_path)


class CapsuleRoute(ImmutableContractModel):
    route_id: Identifier
    path: str
    binding_id: Identifier
    artifact_path: str
    media_type: str = Field(min_length=3, max_length=128)
    fallback_policy: Literal["none", "declared_entry_document"] = "none"
    cache_policy: Literal["immutable", "no_cache"] = "immutable"

    _path = field_validator("path")(_normalize_route_path)
    _artifact_path = field_validator("artifact_path")(_safe_identifier_path)


class CapsuleHostPolicySpec(ImmutableContractModel):
    policy_id: Identifier
    revision: str = Field(pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
    bind_mode: Literal["loopback"] = "loopback"
    allowed_hosts: tuple[Literal["127.0.0.1", "::1"], ...] = ("127.0.0.1",)
    maximum_routes: int = Field(ge=1, le=256)
    maximum_bindings: int = Field(ge=1, le=256)
    maximum_requests: int = Field(ge=1, le=1_000_000)
    maximum_request_path_bytes: int = Field(ge=1, le=8192)
    maximum_response_bytes: int = Field(ge=1, le=134_217_728)
    maximum_session_seconds: int = Field(ge=1, le=86_400)
    idle_timeout_seconds: int = Field(ge=1, le=86_400)
    allowed_methods: tuple[Literal["GET", "HEAD"], ...] = ("GET", "HEAD")
    allowed_media_types: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    security_headers: dict[str, str] = Field(default_factory=dict, max_length=32)

    @field_validator("allowed_hosts")
    @classmethod
    def unique_hosts(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("allowed hosts must be unique")
        return tuple(values)

    @field_validator("allowed_methods")
    @classmethod
    def unique_methods(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("allowed methods must be unique")
        return tuple(values)

    @field_validator("security_headers")
    @classmethod
    def safe_headers(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 32:
            raise ValueError("security headers must be bounded")
        if any(has_secret_like_key(key) for key in value):
            raise ValueError("security headers cannot contain credentials")
        return dict(sorted(value.items()))


class CapsuleHostPolicy(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["CapsuleHostPolicy"]
    metadata: ResourceMetadata
    spec: CapsuleHostPolicySpec
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_identity(self) -> "CapsuleHostPolicy":
        if self.metadata.id != self.spec.policy_id:
            raise ValueError("metadata ID must equal policy ID")
        return self


class CapsuleDefinitionSpec(ContractModel):
    capsule_id: Identifier
    capsule_type: CAPSULE_TYPE = "static_capsule"
    status: CAPSULE_STATUS = "reviewed"


class CapsuleDefinition(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["CapsuleDefinition"]
    metadata: ResourceMetadata
    spec: CapsuleDefinitionSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_identity(self) -> "CapsuleDefinition":
        if self.metadata.id != self.spec.capsule_id:
            raise ValueError("metadata ID must equal capsule ID")
        return self


class CapsuleRevisionProvenance(ImmutableContractModel):
    author_ref: OwnerReference
    source_digest: Digest
    review_ref: Identifier | None = None


class CapsuleRevisionSpec(ImmutableContractModel):
    capsule_id: Identifier
    revision: str = Field(pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
    capsule_type: CAPSULE_TYPE = "static_capsule"
    authoring_manifest_digest: Digest
    artifact_bindings: tuple[CapsuleArtifactBinding, ...] = Field(min_length=1, max_length=64)
    routes: tuple[CapsuleRoute, ...] = Field(min_length=1, max_length=256)
    entry_route: str
    host_policy_ref: Identifier
    revision_digest: Digest
    provenance: CapsuleRevisionProvenance
    status: Literal["reviewed"] = "reviewed"

    _entry_route = field_validator("entry_route")(_normalize_route_path)

    @field_validator("artifact_bindings", "routes")
    @classmethod
    def sort_nested(cls, values):
        if isinstance(values[0], CapsuleArtifactBinding):
            keys = [item.binding_id for item in values]
            if len(set(keys)) != len(keys):
                raise ValueError("artifact binding IDs must be unique")
            mounts = [item.mount_path for item in values]
            if len(set(mounts)) != len(mounts):
                raise ValueError("artifact binding mount paths must be unique")
            ordered = sorted(values, key=lambda item: item.binding_id)
            for left, right in zip(ordered, ordered[1:]):
                if right.mount_path.startswith(left.mount_path.rstrip("/") + "/") or left.mount_path.startswith(right.mount_path.rstrip("/") + "/"):
                    raise ValueError("artifact binding mount paths must not overlap")
            return tuple(ordered)
        keys = [item.route_id for item in values]
        if len(set(keys)) != len(keys):
            raise ValueError("route IDs must be unique")
        paths = [item.path for item in values]
        if len(set(paths)) != len(paths):
            raise ValueError("route paths must be unique")
        ordered = tuple(sorted(values, key=lambda item: _route_path_key(item.path)))
        return ordered

    @model_validator(mode="after")
    def validate_revision(self) -> "CapsuleRevisionSpec":
        routes = {route.path: route for route in self.routes}
        if self.entry_route not in routes:
            raise ValueError("entry route must be declared")
        bindings = {binding.binding_id: binding for binding in self.artifact_bindings}
        for route in self.routes:
            if route.binding_id not in bindings:
                raise ValueError("route binding must be declared")
        return self


class CapsuleRevision(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["CapsuleRevision"]
    metadata: ResourceMetadata
    spec: CapsuleRevisionSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_identity(self) -> "CapsuleRevision":
        if self.metadata.id != f"{self.spec.capsule_id}.{self.spec.revision}":
            raise ValueError("metadata ID must equal capsule ID and revision")
        return self


class CapsuleAuthoringManifestSpec(ContractModel):
    capsule_id: Identifier
    target_revision: str = Field(pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
    bindings: tuple[CapsuleArtifactBinding, ...] = Field(min_length=1, max_length=64)
    routes: tuple[CapsuleRoute, ...] = Field(min_length=1, max_length=256)
    entry_route: str
    host_policy_ref: Identifier
    author_ref: OwnerReference
    source_digest: Digest
    review_ref: Identifier | None = None

    _entry_route = field_validator("entry_route")(_normalize_route_path)

    @model_validator(mode="after")
    def validate_authoring(self) -> "CapsuleAuthoringManifestSpec":
        if self.entry_route not in {route.path for route in self.routes}:
            raise ValueError("entry route must exist in authoring routes")
        if len({item.binding_id for item in self.bindings}) != len(self.bindings):
            raise ValueError("binding IDs must be unique")
        if len({item.path for item in self.routes}) != len(self.routes):
            raise ValueError("route paths must be unique")
        return self


class CapsuleAuthoringManifest(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["CapsuleAuthoringManifest"]
    metadata: ResourceMetadata
    spec: CapsuleAuthoringManifestSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_identity(self) -> "CapsuleAuthoringManifest":
        if self.metadata.id != f"{self.spec.capsule_id}.authoring":
            raise ValueError("metadata ID must equal capsule authoring identifier")
        return self


class CapsuleHostRequestSpec(ContractModel):
    request_id: Identifier
    capsule_id: Identifier
    capsule_revision: str = Field(pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
    caller_context: CallerContext
    host_policy_ref: Identifier
    requested_port: int = Field(default=0, ge=0, le=65535)
    correlation_ref: Identifier | None = None

    @field_validator("requested_port")
    @classmethod
    def bound_port(cls, value: int) -> int:
        if value not in {0} and value < 1024:
            raise ValueError("requested port must be zero or unprivileged")
        return value


class CapsuleHostRequest(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["CapsuleHostRequest"]
    metadata: ResourceMetadata
    spec: CapsuleHostRequestSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_identity(self) -> "CapsuleHostRequest":
        if self.metadata.id != self.spec.request_id:
            raise ValueError("metadata ID must equal host request ID")
        return self


class CapsuleHostSessionSpec(ContractModel):
    session_id: Identifier
    capsule_id: Identifier
    capsule_revision: str = Field(pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
    capsule_digest: Digest
    host: Literal["127.0.0.1", "::1"]
    port: int = Field(ge=0, le=65535)
    base_url: str = Field(min_length=1, max_length=256)
    status: Literal["opening", "open", "closing", "closed", "expired"]
    opened_at: datetime
    expires_at: datetime
    request_budget: ExecutionBudget
    requests_served: int = Field(ge=0)
    artifact_digests: tuple[Digest, ...] = Field(default_factory=tuple, max_length=64)

    @field_validator("opened_at", "expires_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("session timestamps must be timezone-aware")
        return value

    @field_validator("base_url")
    @classmethod
    def loopback_base_url(cls, value: str) -> str:
        if not value.startswith(("http://127.0.0.1:", "http://[::1]:")):
            raise ValueError("base_url must be loopback-local")
        return value

    @model_validator(mode="after")
    def validate_session(self) -> "CapsuleHostSessionSpec":
        if self.expires_at < self.opened_at:
            raise ValueError("session expiry cannot precede opening")
        return self


class CapsuleHostSession(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["CapsuleHostSession"]
    metadata: ResourceMetadata
    spec: CapsuleHostSessionSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_identity(self) -> "CapsuleHostSession":
        if self.metadata.id != self.spec.session_id:
            raise ValueError("metadata ID must equal session ID")
        return self


class CapsuleHostResultSpec(ContractModel):
    status: Literal["success", "partial", "error"]
    session: CapsuleHostSession | None = None
    warnings: tuple[ToolWarning, ...] = Field(default_factory=tuple, max_length=64)
    errors: tuple[ToolError, ...] = Field(default_factory=tuple, max_length=64)
    evidence: tuple[EvidenceRecord, ...] = Field(default_factory=tuple, max_length=64)
    effect_receipts: tuple[EffectReceipt, ...] = Field(default_factory=tuple, max_length=64)
    metrics: dict[str, int] = Field(default_factory=dict, max_length=32)

    @field_validator("metrics")
    @classmethod
    def json_safe_metrics(cls, value: dict[str, int]) -> dict[str, int]:
        if any(has_secret_like_key(key) for key in value):
            raise ValueError("metrics must not expose credential material")
        return dict(sorted(value.items()))

    @model_validator(mode="after")
    def validate_result(self) -> "CapsuleHostResultSpec":
        if self.status == "success":
            if self.session is None or self.errors:
                raise ValueError("successful host results require a session and no errors")
        elif self.status == "partial":
            if self.session is None and not (self.warnings or self.evidence or self.effect_receipts or self.errors):
                raise ValueError("partial host results require observable output")
        else:
            if not self.errors:
                raise ValueError("error host results require ToolError entries")
        return self


class CapsuleHostResult(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["CapsuleHostResult"]
    metadata: ResourceMetadata
    spec: CapsuleHostResultSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}
