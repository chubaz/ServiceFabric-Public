"""Bounded source validation and deterministic text normalization."""

from __future__ import annotations

import hashlib
import mimetypes
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from servicefabric_contracts import SourceBundleManifest


TEXT_TYPES = {"text/html", "text/css", "application/javascript", "application/json", "text/plain"}
ALLOWED_TYPES = TEXT_TYPES | {"image/png", "image/jpeg", "image/webp", "image/x-icon", "font/woff", "font/woff2"}


class SourceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedFile:
    path: str
    media_type: str
    content: bytes
    digest: str


@dataclass(frozen=True)
class ValidatedSourceBundle:
    files: tuple[ValidatedFile, ...]
    source_digest: str
    total_size: int


def normalize_path(value: str) -> str:
    if not value or "\x00" in value or "\\" in value or "//" in value or value.startswith("/"):
        raise SourceValidationError("unsafe source path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SourceValidationError("unsafe source path")
    if ":" in path.parts[0] or len(value) > 512 or any(len(part) > 128 for part in path.parts):
        raise SourceValidationError("unsafe source path")
    return path.as_posix()


def normalize_content(media_type: str, content: bytes) -> bytes:
    if media_type not in TEXT_TYPES:
        return content
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise SourceValidationError("reviewed text source must be UTF-8") from error
    return (text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n").encode("utf-8")


def validate_source(root: Path, manifest: SourceBundleManifest, *, maximum_file_size: int = 4_194_304) -> ValidatedSourceBundle:
    root = root.resolve()
    if len(manifest.files) > 4096:
        raise SourceValidationError("source file count exceeds policy")
    output: list[ValidatedFile] = []
    seen: set[str] = set()
    for item in manifest.files:
        relative = normalize_path(item.path)
        if relative in seen:
            raise SourceValidationError("duplicate normalized source path")
        seen.add(relative)
        path = root / relative
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise SourceValidationError("source entries must be regular non-symlink files")
        if root not in path.resolve().parents:
            raise SourceValidationError("source file escapes root")
        content = path.read_bytes()
        if len(content) > maximum_file_size:
            raise SourceValidationError("source file exceeds size policy")
        guessed = mimetypes.guess_type(relative)[0] or "application/octet-stream"
        if guessed == "text/javascript":
            guessed = "application/javascript"
        if guessed not in ALLOWED_TYPES or guessed != item.media_type:
            raise SourceValidationError("source media type is unsupported or inconsistent")
        raw_digest = "sha256:" + hashlib.sha256(content).hexdigest()
        if raw_digest != item.content_digest:
            raise SourceValidationError("reviewed source digest mismatch")
        normalized = normalize_content(guessed, content)
        output.append(ValidatedFile(relative, guessed, normalized, "sha256:" + hashlib.sha256(normalized).hexdigest()))
    output.sort(key=lambda item: item.path)
    total = sum(len(item.content) for item in output)
    return ValidatedSourceBundle(tuple(output), manifest.source_digest, total)
