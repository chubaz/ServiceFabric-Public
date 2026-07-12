"""Stable build-input and artifact identity calculation."""

from __future__ import annotations

import hashlib
import json

from servicefabric_contracts import ApplicationArtifactManifest, ApplicationRevision

from .builder import BuildOutput, StaticWebBuilder


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def build_spec_digest(revision: ApplicationRevision) -> str:
    return digest(revision.spec.build_spec.model_dump(mode="json"))


def build_input_digest(revision: ApplicationRevision, builder: StaticWebBuilder) -> str:
    return digest({
        "application_id": revision.spec.application_id,
        "application_revision": revision.spec.revision,
        "builder_id": builder.builder_id,
        "builder_revision": builder.builder_revision,
        "build_spec_digest": build_spec_digest(revision),
        "reproducibility": "reproducible",
        "source_digest": revision.spec.source_digest,
    })


def artifact_manifest(revision: ApplicationRevision, output: BuildOutput, builder: StaticWebBuilder) -> ApplicationArtifactManifest:
    files = [
        {"path": path, "content_digest": content_digest, "media_type": media_type, "size_bytes": size}
        for path, content_digest, media_type, size in output.files
    ]
    stable = {
        "application_id": revision.spec.application_id,
        "application_revision": revision.spec.revision,
        "builder_id": builder.builder_id,
        "builder_revision": builder.builder_revision,
        "build_spec_digest": build_spec_digest(revision),
        "entry_document": output.entry_document,
        "files": files,
        "reproducibility": "reproducible",
        "source_digest": revision.spec.source_digest,
        "total_size_bytes": output.total_size,
    }
    artifact_digest = digest(stable)
    artifact_id = "artifact." + artifact_digest.removeprefix("sha256:")[:32]
    return ApplicationArtifactManifest.model_validate({
        "apiVersion": "servicefabric.ai/v1alpha1",
        "kind": "ApplicationArtifactManifest",
        "metadata": {
            "id": artifact_id,
            "name": f"{revision.spec.application_id} {revision.spec.revision}",
            "description": "Immutable deterministic static-web artifact",
            "owner_ref": revision.metadata.owner_ref.model_dump(mode="json"),
        },
        "spec": {
            **stable,
            "artifact_id": artifact_id,
            "artifact_digest": artifact_digest,
            "provenance": {
                "source_manifest_ref": revision.spec.source_bundle_ref,
                "source_digest": revision.spec.source_digest,
                "build_spec_digest": stable["build_spec_digest"],
                "builder_id": builder.builder_id,
                "builder_revision": builder.builder_revision,
            },
        },
    })


def manifest_content_digest(manifest: ApplicationArtifactManifest) -> str:
    spec = manifest.spec
    return digest({
        "application_id": spec.application_id,
        "application_revision": spec.application_revision,
        "builder_id": spec.builder_id,
        "builder_revision": spec.builder_revision,
        "build_spec_digest": spec.build_spec_digest,
        "entry_document": spec.entry_document,
        "files": [item.model_dump(mode="json") for item in spec.files],
        "reproducibility": spec.reproducibility,
        "source_digest": spec.source_digest,
        "total_size_bytes": spec.total_size_bytes,
    })
