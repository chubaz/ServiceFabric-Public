"""File-backed capsule portfolio resolution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from servicefabric_contracts import (
    CapsuleAuthoringManifest,
    CapsuleDefinition,
    CapsuleHostPolicy,
    CapsuleRevision,
)
from servicefabric_contracts.capsules import capsule_authoring_digest, capsule_revision_digest


@dataclass(frozen=True)
class CapsuleResolution:
    definition: CapsuleDefinition
    revision: CapsuleRevision
    authoring_manifest: CapsuleAuthoringManifest
    host_policy: CapsuleHostPolicy
    artifact_digests: tuple[str, ...]


class CapsulePortfolio:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def _load(self, directory: str, name: str) -> dict[str, object]:
        if not name or "/" in name or "\\" in name or ".." in name:
            raise ValueError("invalid capsule resource name")
        path = (self.root / directory / f"{name}.json").resolve()
        if self.root not in path.parents:
            raise ValueError("capsule portfolio path escapes root")
        return json.loads(path.read_text(encoding="utf-8"))

    def definition(self, capsule_id: str) -> CapsuleDefinition:
        return CapsuleDefinition.model_validate(self._load("definitions", capsule_id))

    def revision(self, capsule_id: str, revision: str) -> CapsuleRevision:
        return CapsuleRevision.model_validate(self._load("revisions", f"{capsule_id}-{revision}"))

    def authoring_manifest(self, capsule_id: str, revision: str) -> CapsuleAuthoringManifest:
        return CapsuleAuthoringManifest.model_validate(self._load("authoring", f"{capsule_id}-{revision}"))

    def host_policy(self, policy_id: str) -> CapsuleHostPolicy:
        return CapsuleHostPolicy.model_validate(self._load("host-policies", policy_id))

    def resolve(
        self,
        capsule_id: str,
        revision: str,
        application_portfolio: ApplicationPortfolio,
        artifact_store: FileArtifactStore,
    ) -> CapsuleResolution:
        definition = self.definition(capsule_id)
        revision_model = self.revision(capsule_id, revision)
        authoring = self.authoring_manifest(capsule_id, revision)
        policy = self.host_policy(revision_model.spec.host_policy_ref)
        if definition.spec.status != "reviewed" or revision_model.spec.status != "reviewed":
            raise ValueError("capsule resources must be reviewed")
        if revision_model.spec.capsule_id != definition.spec.capsule_id:
            raise ValueError("definition and revision capsule IDs differ")
        if authoring.spec.capsule_id != revision_model.spec.capsule_id:
            raise ValueError("authoring manifest capsule ID differs")
        if authoring.spec.target_revision != revision_model.spec.revision:
            raise ValueError("authoring manifest revision differs")
        if capsule_authoring_digest(authoring) != revision_model.spec.authoring_manifest_digest:
            raise ValueError("capsule authoring digest mismatch")
        if capsule_revision_digest(revision_model) != revision_model.spec.revision_digest:
            raise ValueError("capsule revision digest mismatch")
        verified: list[str] = []
        for binding in revision_model.spec.artifact_bindings:
            application_portfolio.revision(binding.application_id, binding.application_revision)
            verification = artifact_store.verify_artifact(binding.artifact_digest)
            if not verification.valid:
                raise ValueError(f"artifact {binding.artifact_digest} failed verification")
            manifest = artifact_store.get_manifest(binding.artifact_digest)
            if manifest.spec.application_id != binding.application_id or manifest.spec.application_revision != binding.application_revision:
                raise ValueError("artifact manifest identity mismatch")
            if binding.entry_document not in {item.path for item in manifest.spec.files}:
                raise ValueError("binding entry document is missing from artifact")
            verified.append(binding.artifact_digest)
        return CapsuleResolution(definition, revision_model, authoring, policy, tuple(sorted(verified)))
