"""Immutable and external artifact references."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from .common import ContractModel, Identifier

Digest = Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")]


class OciImageArtifact(ContractModel):
    artifact_kind: Literal["oci_image"]
    image: str = Field(min_length=1, max_length=512)
    digest: Digest


class StaticBundleArtifact(ContractModel):
    artifact_kind: Literal["static_bundle"]
    bundle_ref: str = Field(min_length=1, max_length=512)
    digest: Digest


class ProcessBundleArtifact(ContractModel):
    artifact_kind: Literal["process_bundle"]
    bundle_ref: str = Field(min_length=1, max_length=512)
    digest: Digest


class GraphRevisionArtifact(ContractModel):
    artifact_kind: Literal["graph_revision"]
    graph_revision_ref: str = Field(min_length=3, max_length=256, pattern=r"^[a-z][a-z0-9._:/-]+$")


class ExternalServiceArtifact(ContractModel):
    artifact_kind: Literal["external_service"]
    service_ref: Identifier
    endpoint: str = Field(min_length=8, max_length=512, pattern=r"^https?://")


class ExternalMcpArtifact(ContractModel):
    artifact_kind: Literal["external_mcp"]
    server_ref: Identifier
    endpoint: str = Field(min_length=8, max_length=512, pattern=r"^https?://")


class NoArtifact(ContractModel):
    artifact_kind: Literal["none"]


ArtifactReference = Annotated[
    Union[
        OciImageArtifact,
        StaticBundleArtifact,
        ProcessBundleArtifact,
        GraphRevisionArtifact,
        ExternalServiceArtifact,
        ExternalMcpArtifact,
        NoArtifact,
    ],
    Field(discriminator="artifact_kind"),
]
