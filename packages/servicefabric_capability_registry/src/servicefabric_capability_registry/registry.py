"""Atomic persistence for reviewed static capability declarations.

The registry deliberately stores definitions and application indexes only.  It
does not make a capability callable and does not describe runtime state.
"""

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

from servicefabric_capability_model import CapabilityDefinition


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_STATE_FILE = "capability-registry.json"
_STATE_VERSION = 1


class CapabilityRegistryError(RuntimeError):
    """Base error for static capability registry operations."""


class CapabilityStorageError(CapabilityRegistryError):
    """Raised when a registry location is unsafe or malformed."""


class CapabilityConflictError(CapabilityRegistryError):
    """Raised when an identifier is already bound to different content."""


class CapabilityNotFoundError(CapabilityRegistryError):
    """Raised when a capability identifier is not registered."""


@dataclass(frozen=True)
class CapabilityRecord:
    """A persisted declaration, its stable content digest, and application links."""

    definition: CapabilityDefinition
    digest: str
    application_ids: tuple[str, ...]


@dataclass(frozen=True)
class RegistrationResult:
    """The deterministic outcome of one static registration request."""

    record: CapabilityRecord
    created: bool
    application_link_created: bool


def capability_content_digest(definition: CapabilityDefinition) -> str:
    """Return the SHA-256 digest of canonical, static declaration content."""

    payload = definition.model_dump(mode="json", by_alias=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class CapabilityRegistry:
    """A path-safe local registry for immutable capability declarations."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def register(self, definition: CapabilityDefinition, application_id: str) -> RegistrationResult:
        """Atomically register a definition and link it to one application.

        An existing identical definition is idempotent.  Reusing an identifier
        with different canonical content is rejected without changing storage.
        """

        self._validate_identifier(application_id, "application_id")
        self._validate_definition(definition)
        with self._locked_state() as state:
            capability_id = definition.metadata.id
            digest = capability_content_digest(definition)
            entry = state["capabilities"].get(capability_id)
            created = entry is None
            if entry is not None and entry["digest"] != digest:
                raise CapabilityConflictError(
                    f"capability '{capability_id}' is already registered with different content"
                )
            if entry is None:
                entry = {
                    "definition": definition.model_dump(mode="json", by_alias=True),
                    "digest": digest,
                    "applications": [],
                }
                state["capabilities"][capability_id] = entry
            applications = entry["applications"]
            linked = application_id not in applications
            if linked:
                applications.append(application_id)
                applications.sort()
            index = state["applications"].setdefault(application_id, [])
            if capability_id not in index:
                index.append(capability_id)
                index.sort()
            self._write_state(state)
            return RegistrationResult(self._record(entry), created, linked)

    def list(self, application_id: str | None = None) -> tuple[CapabilityRecord, ...]:
        """List registered declarations in deterministic capability-ID order."""

        if application_id is not None:
            self._validate_identifier(application_id, "application_id")
        state = self._read_state()
        identifiers = (
            state["applications"].get(application_id, [])
            if application_id is not None
            else sorted(state["capabilities"])
        )
        return tuple(self._record(state["capabilities"][identifier]) for identifier in identifiers)

    def describe(self, capability_id: str) -> CapabilityRecord:
        """Describe one static declaration by its capability ID."""

        self._validate_identifier(capability_id, "capability_id")
        state = self._read_state()
        try:
            return self._record(state["capabilities"][capability_id])
        except KeyError as exc:
            raise CapabilityNotFoundError(f"capability '{capability_id}' is not registered") from exc

    def list_capabilities(self, application_id: str | None = None) -> tuple[CapabilityRecord, ...]:
        """Explicit alias for :meth:`list`."""

        return self.list(application_id)

    def describe_capability(self, capability_id: str) -> CapabilityRecord:
        """Explicit alias for :meth:`describe`."""

        return self.describe(capability_id)

    def _validate_definition(self, definition: CapabilityDefinition) -> None:
        if not isinstance(definition, CapabilityDefinition):
            raise TypeError("definition must be a CapabilityDefinition")

    @staticmethod
    def _validate_identifier(value: str, name: str) -> None:
        if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
            raise CapabilityStorageError(f"{name} must be a safe ServiceFabric identifier")

    def _prepare_root(self) -> Path:
        root = self._root
        if root.is_symlink():
            raise CapabilityStorageError("registry root must not be a symlink")
        try:
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as exc:
            raise CapabilityStorageError("registry root is not accessible") from exc
        try:
            status = root.lstat()
        except OSError as exc:
            raise CapabilityStorageError("registry root is not accessible") from exc
        if not root.is_dir() or os.path.islink(root) or not stat.S_ISDIR(status.st_mode):
            raise CapabilityStorageError("registry root must be a real directory")
        return root

    def _read_state(self) -> dict[str, Any]:
        root = self._prepare_root()
        path = root / _STATE_FILE
        if path.is_symlink():
            raise CapabilityStorageError("registry state file must not be a symlink")
        if not path.exists():
            return self._empty_state()
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CapabilityStorageError("registry state file is unreadable") from exc
        self._validate_state(value)
        return value

    def _write_state(self, state: dict[str, Any]) -> None:
        root = self._prepare_root()
        self._validate_state(state)
        path = root / _STATE_FILE
        if path.is_symlink():
            raise CapabilityStorageError("registry state file must not be a symlink")
        descriptor, temporary = tempfile.mkstemp(prefix=".capability-registry-", suffix=".tmp", dir=root)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(state, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except OSError as exc:
            raise CapabilityStorageError("registry state could not be written atomically") from exc
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _locked_state(self):
        return _RegistryLock(self)

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {"version": _STATE_VERSION, "capabilities": {}, "applications": {}}

    @staticmethod
    def _validate_state(state: object) -> None:
        if not isinstance(state, dict) or set(state) != {"version", "capabilities", "applications"}:
            raise CapabilityStorageError("registry state has an unsupported shape")
        if state["version"] != _STATE_VERSION or not isinstance(state["capabilities"], dict) or not isinstance(state["applications"], dict):
            raise CapabilityStorageError("registry state has an unsupported version or index")
        for capability_id, entry in state["capabilities"].items():
            CapabilityRegistry._validate_identifier(capability_id, "capability_id")
            if not isinstance(entry, dict) or set(entry) != {"definition", "digest", "applications"}:
                raise CapabilityStorageError("registry capability entry has an unsupported shape")
            if not isinstance(entry["digest"], str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", entry["digest"]):
                raise CapabilityStorageError("registry capability digest is invalid")
            if not isinstance(entry["applications"], list) or entry["applications"] != sorted(set(entry["applications"])):
                raise CapabilityStorageError("registry application links must be sorted and unique")
            try:
                definition = CapabilityDefinition.model_validate(entry["definition"])
            except Exception as exc:
                raise CapabilityStorageError("registry capability definition is invalid") from exc
            if definition.metadata.id != capability_id:
                raise CapabilityStorageError("registry capability key does not match its definition")
            if capability_content_digest(definition) != entry["digest"]:
                raise CapabilityStorageError("registry capability digest does not match its definition")
            for application_id in entry["applications"]:
                CapabilityRegistry._validate_identifier(application_id, "application_id")
                if capability_id not in state["applications"].get(application_id, []):
                    raise CapabilityStorageError("registry application index is not reciprocal")
        for application_id, capability_ids in state["applications"].items():
            CapabilityRegistry._validate_identifier(application_id, "application_id")
            if not isinstance(capability_ids, list) or capability_ids != sorted(set(capability_ids)):
                raise CapabilityStorageError("registry application index must be sorted and unique")
            if any(capability_id not in state["capabilities"] for capability_id in capability_ids):
                raise CapabilityStorageError("registry application index references an unknown capability")
            if any(application_id not in state["capabilities"][capability_id]["applications"] for capability_id in capability_ids):
                raise CapabilityStorageError("registry capability links are not reciprocal")

    @staticmethod
    def _record(entry: dict[str, Any]) -> CapabilityRecord:
        return CapabilityRecord(
            definition=CapabilityDefinition.model_validate(entry["definition"]),
            digest=entry["digest"],
            application_ids=tuple(entry["applications"]),
        )


class _RegistryLock:
    """A process lock that serializes read-modify-write registration."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry
        self._handle: Any = None
        self._state: dict[str, Any] | None = None

    def __enter__(self) -> dict[str, Any]:
        root = self._registry._prepare_root()
        lock_path = root / ".capability-registry.lock"
        if lock_path.is_symlink():
            raise CapabilityStorageError("registry lock file must not be a symlink")
        try:
            self._handle = lock_path.open("a+", encoding="utf-8")
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
            self._state = self._registry._read_state()
            return self._state
        except OSError as exc:
            raise CapabilityStorageError("registry lock could not be acquired") from exc

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            self._handle.close()
