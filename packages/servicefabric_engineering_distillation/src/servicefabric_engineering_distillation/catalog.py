"""Atomic persistence for reviewed, reusable engineering patterns."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any

import fcntl

from servicefabric_distillation_contracts import DistillationDecision, EngineeringPatternCandidate


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_STATE_FILE = "engineering-pattern-catalog.json"
_STATE_VERSION = 1


class EngineeringPatternCatalogError(RuntimeError):
    """Base error for engineering pattern catalog operations."""


class EngineeringPatternStorageError(EngineeringPatternCatalogError):
    """Raised when catalog storage is unsafe or malformed."""


class EngineeringPatternConflictError(EngineeringPatternCatalogError):
    """Raised when an exact pattern version has different content."""


class EngineeringPatternNotFoundError(EngineeringPatternCatalogError):
    """Raised when a requested exact pattern version is absent."""


@dataclass(frozen=True)
class EngineeringPatternPublication:
    """One immutable pattern candidate published at an exact version."""

    pattern_id: str
    version: str
    candidate: EngineeringPatternCandidate
    decision: DistillationDecision
    digest: str


@dataclass(frozen=True)
class EngineeringPatternPublicationResult:
    """The deterministic outcome of one publication request."""

    publication: EngineeringPatternPublication
    created: bool


def engineering_pattern_content_digest(candidate: EngineeringPatternCandidate) -> str:
    """Return the SHA-256 digest of canonical engineering-pattern content."""

    encoded = json.dumps(
        candidate.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class EngineeringPatternCatalog:
    """A path-safe local catalog of approved, exact-version patterns."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def publish(
        self,
        candidate: EngineeringPatternCandidate,
        decision: DistillationDecision,
        version: str,
    ) -> EngineeringPatternPublicationResult:
        """Atomically publish an approved candidate at one exact version.

        Repeating an identical publication is idempotent. Reusing the same
        pattern ID and version with different candidate content fails without
        changing the catalog.
        """

        self._validate_candidate(candidate)
        self._validate_approval(candidate, decision)
        self._validate_version(version)
        pattern_id = candidate.candidate_id
        digest = engineering_pattern_content_digest(candidate)
        with self._locked_state() as state:
            versions = state["patterns"].setdefault(pattern_id, {})
            entry = versions.get(version)
            created = entry is None
            if entry is not None and entry["digest"] != digest:
                raise EngineeringPatternConflictError(
                    f"engineering pattern '{pattern_id}' version '{version}' already has different content"
                )
            if entry is None:
                entry = {
                    "candidate": candidate.model_dump(mode="json", by_alias=True),
                    "decision": decision.model_dump(mode="json", by_alias=True),
                    "digest": digest,
                }
                versions[version] = entry
                self._write_state(state)
            return EngineeringPatternPublicationResult(self._publication(pattern_id, version, entry), created)

    def describe(self, pattern_id: str, version: str) -> EngineeringPatternPublication:
        """Describe one immutable engineering pattern by exact version."""

        self._validate_identifier(pattern_id, "pattern_id")
        self._validate_version(version)
        state = self._read_state()
        try:
            return self._publication(pattern_id, version, state["patterns"][pattern_id][version])
        except KeyError as exc:
            raise EngineeringPatternNotFoundError(
                f"engineering pattern '{pattern_id}' version '{version}' is not published"
            ) from exc

    def list(self, pattern_id: str | None = None) -> tuple[EngineeringPatternPublication, ...]:
        """List publications in deterministic pattern-ID then version order."""

        if pattern_id is not None:
            self._validate_identifier(pattern_id, "pattern_id")
        state = self._read_state()
        identifiers = (pattern_id,) if pattern_id is not None else tuple(sorted(state["patterns"]))
        return tuple(
            self._publication(identifier, version, state["patterns"][identifier][version])
            for identifier in identifiers
            if identifier in state["patterns"]
            for version in sorted(state["patterns"][identifier])
        )

    def list_patterns(self, pattern_id: str | None = None) -> tuple[EngineeringPatternPublication, ...]:
        """Explicit alias for :meth:`list`."""

        return self.list(pattern_id)

    @staticmethod
    def _validate_candidate(candidate: EngineeringPatternCandidate) -> None:
        if not isinstance(candidate, EngineeringPatternCandidate):
            raise TypeError("candidate must be an EngineeringPatternCandidate")

    @staticmethod
    def _validate_approval(candidate: EngineeringPatternCandidate, decision: DistillationDecision) -> None:
        if not isinstance(decision, DistillationDecision):
            raise TypeError("decision must be a DistillationDecision")
        if decision.decision != "approve" or decision.candidate_ref != candidate.candidate_id:
            raise EngineeringPatternCatalogError("publication requires an approval decision for the candidate")

    @staticmethod
    def _validate_identifier(value: str, name: str) -> None:
        if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
            raise EngineeringPatternStorageError(f"{name} must be a safe ServiceFabric identifier")

    @staticmethod
    def _validate_version(value: str) -> None:
        if (
            not isinstance(value, str)
            or not value
            or len(value) > 128
            or any(character.isspace() for character in value)
            or "/" in value
            or "\\" in value
        ):
            raise EngineeringPatternStorageError("version must be a non-empty exact version without whitespace or path separators")

    def _prepare_root(self) -> Path:
        root = self._root
        if root.is_symlink():
            raise EngineeringPatternStorageError("catalog root must not be a symlink")
        try:
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
            status = root.lstat()
        except OSError as exc:
            raise EngineeringPatternStorageError("catalog root is not accessible") from exc
        if not root.is_dir() or os.path.islink(root) or not stat.S_ISDIR(status.st_mode):
            raise EngineeringPatternStorageError("catalog root must be a real directory")
        return root

    def _read_state(self) -> dict[str, Any]:
        root = self._prepare_root()
        path = root / _STATE_FILE
        if path.is_symlink():
            raise EngineeringPatternStorageError("catalog state file must not be a symlink")
        if not path.exists():
            return self._empty_state()
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EngineeringPatternStorageError("catalog state file is unreadable") from exc
        self._validate_state(value)
        return value

    def _write_state(self, state: dict[str, Any]) -> None:
        root = self._prepare_root()
        self._validate_state(state)
        path = root / _STATE_FILE
        if path.is_symlink():
            raise EngineeringPatternStorageError("catalog state file must not be a symlink")
        descriptor, temporary = tempfile.mkstemp(prefix=".engineering-pattern-catalog-", suffix=".tmp", dir=root)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(state, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except OSError as exc:
            raise EngineeringPatternStorageError("catalog state could not be written atomically") from exc
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _locked_state(self):
        return _CatalogLock(self)

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {"version": _STATE_VERSION, "patterns": {}}

    @classmethod
    def _validate_state(cls, state: object) -> None:
        if not isinstance(state, dict) or set(state) != {"version", "patterns"}:
            raise EngineeringPatternStorageError("catalog state has an unsupported shape")
        if state["version"] != _STATE_VERSION or not isinstance(state["patterns"], dict):
            raise EngineeringPatternStorageError("catalog state has an unsupported version or index")
        for pattern_id, versions in state["patterns"].items():
            cls._validate_identifier(pattern_id, "pattern_id")
            if not isinstance(versions, dict) or not versions:
                raise EngineeringPatternStorageError("catalog pattern versions must be a non-empty object")
            for version, entry in versions.items():
                cls._validate_version(version)
                if not isinstance(entry, dict) or set(entry) != {"candidate", "decision", "digest"}:
                    raise EngineeringPatternStorageError("catalog publication has an unsupported shape")
                if not isinstance(entry["digest"], str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", entry["digest"]):
                    raise EngineeringPatternStorageError("catalog publication digest is invalid")
                try:
                    candidate = EngineeringPatternCandidate.model_validate(entry["candidate"])
                    decision = DistillationDecision.model_validate(entry["decision"])
                except Exception as exc:
                    raise EngineeringPatternStorageError("catalog publication contracts are invalid") from exc
                if candidate.candidate_id != pattern_id:
                    raise EngineeringPatternStorageError("catalog pattern key does not match its candidate")
                cls._validate_approval(candidate, decision)
                if engineering_pattern_content_digest(candidate) != entry["digest"]:
                    raise EngineeringPatternStorageError("catalog publication digest does not match its candidate")

    @staticmethod
    def _publication(pattern_id: str, version: str, entry: dict[str, Any]) -> EngineeringPatternPublication:
        return EngineeringPatternPublication(
            pattern_id=pattern_id,
            version=version,
            candidate=EngineeringPatternCandidate.model_validate(entry["candidate"]),
            decision=DistillationDecision.model_validate(entry["decision"]),
            digest=entry["digest"],
        )


class _CatalogLock:
    """A process lock that serializes catalog reads and writes."""

    def __init__(self, catalog: EngineeringPatternCatalog) -> None:
        self._catalog = catalog
        self._handle: Any = None
        self._state: dict[str, Any] | None = None

    def __enter__(self) -> dict[str, Any]:
        root = self._catalog._prepare_root()
        lock_path = root / ".engineering-pattern-catalog.lock"
        if lock_path.is_symlink():
            raise EngineeringPatternStorageError("catalog lock file must not be a symlink")
        try:
            self._handle = lock_path.open("a+", encoding="utf-8")
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
            self._state = self._catalog._read_state()
            return self._state
        except OSError as exc:
            raise EngineeringPatternStorageError("catalog lock could not be acquired") from exc

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            self._handle.close()
