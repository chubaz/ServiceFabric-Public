"""Internal in-process application builder service boundary."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio, StaticWebBuilder, artifact_manifest, build_input_digest, validate_source
from servicefabric_contracts import ApplicationBuildRequest, ApplicationBuildResult


class ApplicationBuilderService:
    def __init__(self, portfolio: ApplicationPortfolio, store: FileArtifactStore):
        self.portfolio = portfolio
        self.store = store
        self.builder = StaticWebBuilder()

    def list_applications(self) -> tuple[str, ...]:
        return tuple(sorted(path.stem for path in (self.portfolio.root / "definitions").glob("*.json")))

    def describe_application(self, application_id: str):
        return self.portfolio.definition(application_id)

    def build_application(self, request: ApplicationBuildRequest) -> ApplicationBuildResult:
        try:
            definition = self.portfolio.definition(request.spec.application_id)
            revision = self.portfolio.revision(request.spec.application_id, request.spec.revision)
            if definition.spec.status != "reviewed":
                raise ValueError("application definition is not reviewed")
            source_manifest = self.portfolio.verify_source(revision)
            source = validate_source(self.portfolio.source_root(revision.spec.source_bundle_ref), source_manifest)
            with tempfile.TemporaryDirectory(prefix="servicefabric-build-") as temporary:
                output = self.builder.build(revision, source, Path(temporary) / "output")
                manifest = artifact_manifest(revision, output, self.builder)
                self.store.put_artifact(manifest, output.output_root)
            build_id = "build." + build_input_digest(revision, self.builder)[7:39]
            now = datetime.now(timezone.utc)
            return ApplicationBuildResult.model_validate({
                "apiVersion": "servicefabric.ai/v1alpha1",
                "kind": "ApplicationBuildResult",
                "status": "success",
                "application_id": revision.spec.application_id,
                "revision": revision.spec.revision,
                "build_id": build_id,
                "artifact_ref": manifest.spec.artifact_id,
                "artifact_digest": manifest.spec.artifact_digest,
                "artifact_manifest_ref": manifest.spec.artifact_id,
                "evidence": [{
                    "evidence_id": "evidence." + manifest.spec.artifact_digest[7:39],
                    "evidence_type": "artifact",
                    "source_ref": manifest.spec.artifact_id,
                    "locator": manifest.spec.artifact_id,
                    "content_digest": manifest.spec.artifact_digest,
                    "collected_at": now,
                    "trust_classification": "platform",
                    "claims": ["artifact content verified"],
                    "summary": "The immutable static-web artifact was published and verified.",
                    "provenance_refs": [revision.spec.source_bundle_ref],
                }],
                "metrics": {"files": len(manifest.spec.files), "bytes": manifest.spec.total_size_bytes},
            })
        except Exception as error:
            return ApplicationBuildResult.model_validate({
                "apiVersion": "servicefabric.ai/v1alpha1",
                "kind": "ApplicationBuildResult",
                "status": "error",
                "application_id": request.spec.application_id,
                "revision": request.spec.revision,
                "build_id": "build.failed",
                "errors": [{
                    "code": "SF-EXEC-APPLICATION_BUILD_FAILED",
                    "category": "execution",
                    "message": "Application build failed validation or execution.",
                    "details": {"failure_type": type(error).__name__},
                }],
            })

    def get_artifact_manifest(self, artifact_digest: str):
        return self.store.get_manifest(artifact_digest)

    def verify_artifact(self, artifact_digest: str):
        return self.store.verify_artifact(artifact_digest)

    def open_artifact_file(self, artifact_digest: str, relative: str) -> bytes:
        return self.store.open_file(artifact_digest, relative)
