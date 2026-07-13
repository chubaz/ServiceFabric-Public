"""Atomic immutable content-addressed artifact storage."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from servicefabric_contracts import ApplicationArtifactManifest
from servicefabric_builder.identity import manifest_content_digest


class ArtifactIntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactVerification:
    valid: bool
    artifact_digest: str
    verified_files: tuple[str, ...]
    missing_files: tuple[str, ...] = ()
    unexpected_files: tuple[str, ...] = ()
    digest_mismatches: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class FileArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _directory(self, artifact_digest: str) -> Path:
        if not artifact_digest.startswith("sha256:") or len(artifact_digest) != 71:
            raise ValueError("invalid artifact digest")
        value = artifact_digest[7:]
        if any(character not in "0123456789abcdef" for character in value):
            raise ValueError("invalid artifact digest")
        return self.root / "sha256" / value[:2] / value

    def put_artifact(self, manifest: ApplicationArtifactManifest, source_root: Path) -> str:
        if manifest_content_digest(manifest) != manifest.spec.artifact_digest:
            raise ArtifactIntegrityError("artifact manifest identity is inconsistent")
        final = self._directory(manifest.spec.artifact_digest)
        if final.exists():
            verification = self.verify_artifact(manifest.spec.artifact_digest)
            if not verification.valid:
                raise ArtifactIntegrityError("existing artifact is inconsistent")
            return manifest.spec.artifact_digest
        final.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".publish-", dir=final.parent))
        try:
            files_root = temporary / "files"
            files_root.mkdir()
            for item in manifest.spec.files:
                source = source_root / item.path
                destination = files_root / item.path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            (temporary / "manifest.json").write_text(
                json.dumps(manifest.model_dump(mode="json", by_alias=True), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            for path in temporary.rglob("*"):
                if path.is_file():
                    path.chmod(0o444)
            os.rename(temporary, final)
        except FileExistsError:
            shutil.rmtree(temporary, ignore_errors=True)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        verification = self.verify_artifact(manifest.spec.artifact_digest)
        if not verification.valid:
            raise ArtifactIntegrityError("published artifact failed verification")
        return manifest.spec.artifact_digest

    def get_manifest(self, artifact_digest: str) -> ApplicationArtifactManifest:
        path = self._directory(artifact_digest) / "manifest.json"
        if not path.is_file():
            raise FileNotFoundError("artifact not found")
        return ApplicationArtifactManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def list_artifacts(self) -> tuple[str, ...]:
        """List only complete immutable artifacts, in deterministic digest order."""
        root = self.root / "sha256"
        if not root.is_dir():
            return ()
        digests = []
        for manifest_path in root.glob("*/*/manifest.json"):
            digest = "sha256:" + manifest_path.parent.name
            try:
                self.get_manifest(digest)
            except (FileNotFoundError, ValueError):
                continue
            digests.append(digest)
        return tuple(sorted(digests))

    def open_file(self, artifact_digest: str, relative: str) -> bytes:
        path = PurePosixPath(relative)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("unsafe artifact path")
        root = self._directory(artifact_digest) / "files"
        target = root.joinpath(*path.parts)
        manifest = self.get_manifest(artifact_digest)
        if relative not in {item.path for item in manifest.spec.files}:
            raise FileNotFoundError("artifact file not declared")
        return target.read_bytes()

    def verify_artifact(self, artifact_digest: str) -> ArtifactVerification:
        try:
            manifest = self.get_manifest(artifact_digest)
        except (FileNotFoundError, ValueError) as error:
            return ArtifactVerification(False, artifact_digest, (), errors=(str(error),))
        root = self._directory(artifact_digest) / "files"
        declared = {item.path: item for item in manifest.spec.files}
        actual = {path.relative_to(root).as_posix(): path for path in root.rglob("*") if path.is_file()}
        missing = tuple(sorted(set(declared) - set(actual)))
        unexpected = tuple(sorted(set(actual) - set(declared)))
        mismatches = []
        verified = []
        for relative in sorted(set(declared) & set(actual)):
            item = declared[relative]
            content = actual[relative].read_bytes()
            value = "sha256:" + hashlib.sha256(content).hexdigest()
            if value != item.content_digest or len(content) != item.size_bytes:
                mismatches.append(relative)
            else:
                verified.append(relative)
        errors = []
        if manifest_content_digest(manifest) != artifact_digest:
            errors.append("artifact manifest digest mismatch")
        if sum(item.size_bytes for item in manifest.spec.files) != manifest.spec.total_size_bytes:
            errors.append("artifact total size mismatch")
        valid = not (missing or unexpected or mismatches or errors)
        return ArtifactVerification(valid, artifact_digest, tuple(verified), missing, unexpected, tuple(mismatches), tuple(errors))
