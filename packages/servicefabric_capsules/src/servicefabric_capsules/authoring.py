"""Declarative capsule authoring and publication."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from servicefabric_contracts import (
    CapsuleAuthoringManifest,
    CapsuleRevision,
)
from servicefabric_contracts.capsules import capsule_authoring_digest, capsule_revision_digest
from .portfolio import CapsulePortfolio


@dataclass(frozen=True)
class CapsuleAuthoringDiagnostic:
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    source_pointer: str | None = None
    canonical_pointer: str | None = None
    remediation: str | None = None


@dataclass(frozen=True)
class CapsuleAuthoringResult:
    status: Literal["published", "reused", "requires_review", "invalid", "unsafe"]
    revision: CapsuleRevision | None
    diagnostics: tuple[CapsuleAuthoringDiagnostic, ...]
    evidence: tuple[dict[str, object], ...]
    artifact_digests: tuple[str, ...]
    revision_digest: str | None


class CapsuleAuthoringService:
    def __init__(self, portfolio: CapsulePortfolio, application_portfolio: ApplicationPortfolio, artifact_store: FileArtifactStore):
        self.portfolio = portfolio
        self.application_portfolio = application_portfolio
        self.artifact_store = artifact_store

    def author(self, manifest: CapsuleAuthoringManifest) -> CapsuleAuthoringResult:
        diagnostics: list[CapsuleAuthoringDiagnostic] = []
        evidence: list[dict[str, object]] = []
        definition = self.portfolio.definition(manifest.spec.capsule_id)
        if definition.spec.status != "reviewed":
            diagnostics.append(CapsuleAuthoringDiagnostic("CAPSULE_NOT_REVIEWED", "error", "capsule definition must be reviewed"))
        try:
            policy = self.portfolio.host_policy(manifest.spec.host_policy_ref)
        except Exception as error:
            diagnostics.append(CapsuleAuthoringDiagnostic("CAPSULE_HOST_POLICY_MISSING", "error", str(error)))
            return CapsuleAuthoringResult("invalid", None, tuple(diagnostics), tuple(evidence), (), None)

        if diagnostics:
            return CapsuleAuthoringResult("invalid", None, tuple(diagnostics), tuple(evidence), (), None)
        artifact_digests = []
        for binding in manifest.spec.bindings:
            artifact_digests.append(binding.artifact_digest)
            self.application_portfolio.revision(binding.application_id, binding.application_revision)
            verification = self.artifact_store.verify_artifact(binding.artifact_digest)
            if not verification.valid:
                diagnostics.append(CapsuleAuthoringDiagnostic("CAPSULE_ARTIFACT_INVALID", "error", f"artifact {binding.artifact_digest} failed verification"))
                continue
            manifest_record = self.artifact_store.get_manifest(binding.artifact_digest)
            if manifest_record.spec.application_id != binding.application_id or manifest_record.spec.application_revision != binding.application_revision:
                diagnostics.append(CapsuleAuthoringDiagnostic("CAPSULE_ARTIFACT_MISMATCH", "error", f"artifact {binding.artifact_digest} does not match the reviewed application revision"))
                continue
            evidence.append(
                {
                    "evidence_id": f"evidence.{binding.binding_id}",
                    "evidence_type": "artifact",
                    "source_ref": binding.artifact_manifest_ref,
                    "locator": binding.artifact_digest,
                    "content_digest": binding.artifact_digest,
                    "trust_classification": "platform",
                    "summary": f"artifact {binding.artifact_digest} verified for capsule binding {binding.binding_id}",
                }
            )

        if diagnostics:
            return CapsuleAuthoringResult("unsafe", None, tuple(diagnostics), tuple(evidence), tuple(sorted(artifact_digests)), None)

        revision = CapsuleRevision.model_validate(
            {
                "apiVersion": "servicefabric.ai/v1alpha1",
                "kind": "CapsuleRevision",
                "metadata": {
                    "id": f"{manifest.spec.capsule_id}.{manifest.spec.target_revision}",
                    "name": f"{definition.metadata.name} {manifest.spec.target_revision}",
                    "description": definition.metadata.description,
                    "labels": dict(definition.metadata.labels),
                    "annotations": dict(definition.metadata.annotations),
                    "owner_ref": definition.metadata.owner_ref.model_dump(mode="json"),
                },
                "spec": {
                    "capsule_id": manifest.spec.capsule_id,
                    "revision": manifest.spec.target_revision,
                    "capsule_type": "static_capsule",
                    "authoring_manifest_digest": capsule_authoring_digest(manifest),
                    "artifact_bindings": [binding.model_dump(mode="json", by_alias=True) for binding in manifest.spec.bindings],
                    "routes": [route.model_dump(mode="json", by_alias=True) for route in manifest.spec.routes],
                    "entry_route": manifest.spec.entry_route,
                    "host_policy_ref": policy.spec.policy_id,
                    "revision_digest": "sha256:" + ("0" * 64),
                    "provenance": {
                        "author_ref": manifest.spec.author_ref.model_dump(mode="json"),
                        "source_digest": manifest.spec.source_digest,
                        "review_ref": manifest.spec.review_ref,
                    },
                    "status": "reviewed",
                },
            }
        )
        revision_digest = capsule_revision_digest(revision)
        revision = revision.model_copy(update={"spec": revision.spec.model_copy(update={"revision_digest": revision_digest})})
        revision_digest = capsule_revision_digest(revision)
        return self._publish_revision(revision, tuple(sorted(artifact_digests)), tuple(evidence), revision_digest)

    def _publish_revision(
        self,
        revision: CapsuleRevision,
        artifact_digests: tuple[str, ...],
        evidence: tuple[dict[str, object], ...],
        revision_digest: str,
    ) -> CapsuleAuthoringResult:
        revisions = self.portfolio.root / "revisions"
        revisions.mkdir(parents=True, exist_ok=True)
        path = revisions / f"{revision.spec.capsule_id}-{revision.spec.revision}.json"
        payload = json.dumps(revision.model_dump(mode="json", by_alias=True), indent=2, sort_keys=True) + "\n"
        if path.exists():
            existing = CapsuleRevision.model_validate_json(path.read_text(encoding="utf-8"))
            if capsule_revision_digest(existing) != revision_digest:
                raise ValueError("capsule revision already exists with different digest")
            return CapsuleAuthoringResult("reused", existing, (), evidence, artifact_digests, revision_digest)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=revisions, prefix=".capsule-", delete=False) as handle:
            handle.write(payload)
            temporary_path = Path(handle.name)
        try:
            os.replace(temporary_path, path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink(missing_ok=True)
        return CapsuleAuthoringResult("published", revision, (), evidence, artifact_digests, revision_digest)
