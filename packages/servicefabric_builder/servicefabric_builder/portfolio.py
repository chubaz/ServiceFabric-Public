"""File-backed reviewed application portfolio."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from servicefabric_contracts import ApplicationDefinition, ApplicationRevision, SourceBundleManifest


class ApplicationPortfolio:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def _load(self, directory: str, name: str) -> dict[str, object]:
        if not name or "/" in name or "\\" in name or ".." in name:
            raise ValueError("invalid portfolio resource name")
        path = (self.root / directory / f"{name}.json").resolve()
        if self.root not in path.parents:
            raise ValueError("portfolio path escapes root")
        return json.loads(path.read_text(encoding="utf-8"))

    def definition(self, application_id: str) -> ApplicationDefinition:
        return ApplicationDefinition.model_validate(self._load("definitions", application_id))

    def revision(self, application_id: str, revision: str) -> ApplicationRevision:
        return ApplicationRevision.model_validate(self._load("revisions", f"{application_id}-{revision}"))

    def source_manifest(self, source_ref: str) -> SourceBundleManifest:
        return SourceBundleManifest.model_validate(self._load("source-manifests", source_ref))

    def source_root(self, source_ref: str) -> Path:
        path = (self.root / "sources" / source_ref).resolve()
        if self.root not in path.parents:
            raise ValueError("source path escapes portfolio")
        return path

    def verify_source(self, revision: ApplicationRevision) -> SourceBundleManifest:
        manifest = self.source_manifest(revision.spec.source_bundle_ref)
        if manifest.source_digest != revision.spec.source_digest:
            raise ValueError("revision and source manifest digests differ")
        root = self.source_root(revision.spec.source_bundle_ref)
        declared = {item.path: item for item in manifest.files}
        actual = {
            path.relative_to(root).as_posix(): path
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if set(actual) != set(declared):
            raise ValueError("source files do not match reviewed manifest")
        for relative, path in actual.items():
            digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != declared[relative].content_digest or path.stat().st_size != declared[relative].size_bytes:
                raise ValueError(f"source integrity mismatch: {relative}")
        return manifest
