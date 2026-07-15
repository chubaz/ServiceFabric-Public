"""Crash-safe registration of already-validated static capability definitions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable, Mapping


class CapabilityRegistryError(RuntimeError):
    """Base error for registry failures."""


class CapabilityConflictError(CapabilityRegistryError):
    """A capability identifier is already registered with different content."""


class CapabilityNotFoundError(CapabilityRegistryError):
    """The requested static capability is not registered."""


class CorruptCapabilityRecordError(CapabilityRegistryError):
    """A registry record cannot be trusted or decoded."""


@dataclass(frozen=True, slots=True)
class RegistryRecord:
    """The persisted identity of a capability definition."""

    capability_id: str
    digest: str
    definition: Any


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _json_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_none=False)
    if hasattr(value, "to_dict"):
        return _json_value(value.to_dict())
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict

        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _field(definition: Any, names: Iterable[str]) -> str | None:
    names = tuple(names)
    if isinstance(definition, Mapping):
        for name in names:
            value = definition.get(name)
            if isinstance(value, str):
                return value
    for name in names:
        value = getattr(definition, name, None)
        if isinstance(value, str):
            return value
    for nested_name in ("spec", "metadata"):
        nested = definition.get(nested_name) if isinstance(definition, Mapping) else getattr(definition, nested_name, None)
        if nested is not None:
            found = _field(nested, names)
            if found:
                return found
    return None


def _require_identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise CapabilityRegistryError(f"invalid {label}")
    return value


class CapabilityRegistry:
    """A deterministic registry of static capability definitions.

    Definitions are immutable records. Registration uses an exclusive lock,
    canonical JSON, a digest envelope, and fsync-backed replacement. No
    runtime state or executable handler is stored here.
    """

    def __init__(self, root: Path):
        root = Path(root)
        if root.exists() and root.is_symlink():
            raise CapabilityRegistryError("registry root cannot be a symlink")
        self.root = root.resolve(strict=False)
        self.records_dir = self.root / "capabilities"
        self.index_dir = self.root / "applications"
        self.lock_dir = self.root / ".locks"
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise CapabilityRegistryError("registry root cannot be a symlink")
        self._thread_lock = threading.RLock()

    @staticmethod
    def _key(identifier: str) -> str:
        return hashlib.sha256(identifier.encode("utf-8")).hexdigest()

    def _record_path(self, capability_id: str) -> Path:
        return self.records_dir / (self._key(capability_id) + ".json")

    def _lock_path(self, key: str) -> Path:
        return self.lock_dir / (key + ".lock")

    def _atomic_write(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=path.parent, prefix=".pending-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)

    def _read_payload(self, path: Path) -> tuple[dict[str, Any], Any]:
        if path.is_symlink():
            raise CorruptCapabilityRecordError("capability record is a symlink")
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            payload = envelope["payload"]
            if envelope["digest"] != _digest(payload):
                raise CorruptCapabilityRecordError("capability record digest mismatch")
            return envelope, payload
        except CorruptCapabilityRecordError:
            raise
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CorruptCapabilityRecordError("capability record is unreadable") from exc

    def _lock(self, key: str):
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        path = self._lock_path(key)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise CapabilityConflictError("capability registration is already in progress") from exc
        os.close(fd)
        return path

    def register(self, definition: Any) -> RegistryRecord:
        payload = _json_value(definition)
        if not isinstance(payload, dict):
            raise CapabilityRegistryError("capability definition must serialize to an object")
        capability_id = _require_identifier(_field(definition, ("capability_id", "capabilityId", "id")) or _field(payload, ("capability_id", "capabilityId", "id")), "capability identifier")
        application_id = _field(definition, ("application_id", "applicationId")) or _field(payload, ("application_id", "applicationId"))
        key = self._key(capability_id)
        with self._thread_lock:
            lock_path = self._lock(key)
            try:
                path = self._record_path(capability_id)
                if path.exists():
                    _, existing = self._read_payload(path)
                    if existing != payload:
                        raise CapabilityConflictError(f"capability '{capability_id}' conflicts with the registered definition")
                else:
                    envelope = {"digest": _digest(payload), "payload": payload}
                    self._atomic_write(path, _canonical(envelope))
                if application_id:
                    self._update_application_index(application_id, capability_id)
                return RegistryRecord(capability_id, _digest(payload), payload)
            finally:
                lock_path.unlink(missing_ok=True)

    def _update_application_index(self, application_id: str, capability_id: str) -> None:
        application_id = _require_identifier(application_id, "application identifier")
        lock_path = self._lock(self._key("application-index:" + application_id))
        try:
            path = self.index_dir / (self._key(application_id) + ".json")
            if path.is_symlink():
                raise CorruptCapabilityRecordError("application capability index is a symlink")
            values: list[str] = []
            if path.exists():
                try:
                    values = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError, TypeError) as exc:
                    raise CorruptCapabilityRecordError("application capability index is unreadable") from exc
            if capability_id not in values:
                values.append(capability_id)
            self._atomic_write(path, _canonical(sorted(values)))
        finally:
            lock_path.unlink(missing_ok=True)

    def describe(self, capability_id: str) -> Any:
        capability_id = _require_identifier(capability_id, "capability identifier")
        path = self._record_path(capability_id)
        if not path.is_file():
            raise CapabilityNotFoundError(f"capability '{capability_id}' is not registered")
        _, payload = self._read_payload(path)
        return payload

    def list(self, application_id: str | None = None) -> tuple[dict[str, Any], ...]:
        ids: list[str] | None = None
        if application_id is not None:
            application_id = _require_identifier(application_id, "application identifier")
            path = self.index_dir / (self._key(application_id) + ".json")
            if not path.is_file():
                return ()
            try:
                ids = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError) as exc:
                raise CorruptCapabilityRecordError("application capability index is unreadable") from exc
        paths = [self._record_path(identifier) for identifier in ids] if ids is not None else sorted(self.records_dir.glob("*.json")) if self.records_dir.is_dir() else []
        records = []
        for path in paths:
            if path.is_file():
                _, payload = self._read_payload(path)
                records.append(payload)
        return tuple(sorted(records, key=lambda item: _field(item, ("capability_id", "capabilityId", "id")) or ""))
