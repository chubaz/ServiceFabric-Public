"""Crash-safe local single-process operation store with immutable event history."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from servicefabric_contracts import OperationEvent, OperationTransition, ServiceFabricOperation


class OperationStoreError(RuntimeError):
    pass


class OperationConflictError(OperationStoreError):
    pass


class CorruptOperationError(OperationStoreError):
    pass


@dataclass(frozen=True, slots=True)
class StoreLimits:
    maximum_operations: int = 1000
    maximum_events_per_operation: int = 1000
    maximum_record_bytes: int = 1_048_576


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _envelope(payload: object) -> bytes:
    return canonical_json({"digest": digest_bytes(canonical_json(payload)), "payload": payload})


class DurableOperationStore:
    def __init__(self, root: Path, *, limits: StoreLimits = StoreLimits()):
        self._root = root.resolve(strict=False)
        if root.exists() and root.is_symlink():
            raise OperationStoreError("store root cannot be a symlink")
        self._root.mkdir(parents=True, exist_ok=True)
        if self._root.is_symlink():
            raise OperationStoreError("store root cannot be a symlink")
        self._limits = limits
        self._lock = threading.RLock()

    @staticmethod
    def _key(operation_id: str) -> str:
        if not operation_id or len(operation_id) > 128:
            raise OperationStoreError("invalid operation identifier")
        return hashlib.sha256(operation_id.encode("utf-8")).hexdigest()

    def _operation_dir(self, operation_id: str) -> Path:
        path = self._root / self._key(operation_id)
        if path.exists() and path.is_symlink():
            raise CorruptOperationError("operation path is a symlink")
        return path

    def _atomic_write(self, path: Path, content: bytes, *, exclusive: bool = False) -> None:
        if len(content) > self._limits.maximum_record_bytes:
            raise OperationStoreError("record exceeds configured size limit")
        path.parent.mkdir(parents=True, exist_ok=True)
        if exclusive and path.exists():
            raise OperationConflictError("immutable record already exists")
        with NamedTemporaryFile(dir=path.parent, prefix=".pending-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            if exclusive and path.exists():
                raise OperationConflictError("immutable record already exists")
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)

    def _read(self, path: Path) -> object:
        try:
            content = path.read_bytes()
            if len(content) > self._limits.maximum_record_bytes:
                raise CorruptOperationError("record exceeds configured size limit")
            envelope = json.loads(content)
            payload = envelope["payload"]
            if envelope["digest"] != digest_bytes(canonical_json(payload)):
                raise CorruptOperationError("record digest mismatch")
            return payload
        except CorruptOperationError:
            raise
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CorruptOperationError("operation record is unreadable") from exc

    def publish(self, operation: ServiceFabricOperation, initial_event: OperationEvent) -> None:
        if initial_event.spec.sequence != 1 or initial_event.spec.operation_ref != operation.spec.operation_id:
            raise OperationStoreError("initial event does not match operation")
        with self._lock:
            existing = [path for path in self._root.iterdir() if path.is_dir()]
            if len(existing) >= self._limits.maximum_operations:
                raise OperationStoreError("operation retention limit reached")
            directory = self._operation_dir(operation.spec.operation_id)
            if directory.exists():
                raise OperationConflictError("operation already exists")
            directory.mkdir()
            (directory / "events").mkdir()
            initial_payload = operation.model_dump(mode="json", by_alias=True)
            self._atomic_write(directory / "initial.json", _envelope(initial_payload), exclusive=True)
            self._atomic_write(directory / "events" / "00000001.json", _envelope({"event": initial_event.model_dump(mode="json", by_alias=True)}), exclusive=True)
            self._write_snapshot(directory, operation, 1)

    def _write_snapshot(self, directory: Path, operation: ServiceFabricOperation, version: int) -> None:
        self._atomic_write(directory / "snapshot.json", _envelope({"version": version, "operation": operation.model_dump(mode="json", by_alias=True)}))

    def get(self, operation_id: str) -> tuple[ServiceFabricOperation, int]:
        directory = self._operation_dir(operation_id)
        payload = self._read(directory / "snapshot.json")
        operation = ServiceFabricOperation.model_validate(payload["operation"])
        if operation.spec.operation_id != operation_id:
            raise CorruptOperationError("snapshot operation identity mismatch")
        return operation, int(payload["version"])

    def append(self, transition: OperationTransition, event: OperationEvent, resulting: ServiceFabricOperation, *, expected_version: int) -> int:
        with self._lock:
            current, version = self.get(transition.spec.operation_ref)
            if version != expected_version or transition.spec.expected_version != expected_version:
                raise OperationConflictError("stale operation version")
            if current.spec.state != transition.spec.from_state:
                raise OperationConflictError("stale operation state")
            if transition.spec.resulting_version != event.spec.sequence or event.spec.operation_version != transition.spec.resulting_version:
                raise OperationStoreError("event and transition versions differ")
            if resulting.spec.operation_id != current.spec.operation_id or resulting.spec.state != transition.spec.to_state:
                raise OperationStoreError("resulting snapshot does not match transition")
            if event.spec.transition_ref != transition.spec.transition_id or event.spec.operation_ref != current.spec.operation_id:
                raise OperationStoreError("event does not bind the transition")
            if version >= self._limits.maximum_events_per_operation:
                raise OperationStoreError("event retention limit reached")
            directory = self._operation_dir(current.spec.operation_id)
            event_path = directory / "events" / f"{event.spec.sequence:08d}.json"
            payload = {"event": event.model_dump(mode="json", by_alias=True), "transition": transition.model_dump(mode="json", by_alias=True)}
            self._atomic_write(event_path, _envelope(payload), exclusive=True)
            self._write_snapshot(directory, resulting, transition.spec.resulting_version)
            return transition.spec.resulting_version

    def events(self, operation_id: str) -> tuple[OperationEvent, ...]:
        directory = self._operation_dir(operation_id)
        paths = sorted((directory / "events").glob("*.json"))
        events: list[OperationEvent] = []
        previous_digest = None
        for sequence, path in enumerate(paths, start=1):
            payload = self._read(path)
            event = OperationEvent.model_validate(payload["event"])
            if event.spec.operation_ref != operation_id or event.spec.sequence != sequence:
                raise CorruptOperationError("operation event sequence is corrupt")
            if event.spec.previous_event_digest != previous_digest:
                raise CorruptOperationError("operation event digest chain is corrupt")
            previous_digest = event.spec.event_digest
            events.append(event)
        if not events:
            raise CorruptOperationError("operation has no event history")
        return tuple(events)

    def replay(self, operation_id: str) -> tuple[ServiceFabricOperation, int]:
        directory = self._operation_dir(operation_id)
        initial = ServiceFabricOperation.model_validate(self._read(directory / "initial.json"))
        events = self.events(operation_id)
        operation = initial
        for path in sorted((directory / "events").glob("*.json"))[1:]:
            payload = self._read(path)
            transition = OperationTransition.model_validate(payload["transition"])
            if operation.spec.state != transition.spec.from_state:
                raise CorruptOperationError("transition history state mismatch")
            updates = {"state": transition.spec.to_state, "updated_at": transition.spec.transitioned_at}
            if transition.spec.to_state in {"succeeded", "partially_succeeded", "failed", "cancelled", "timed_out"}:
                updates["completed_at"] = transition.spec.transitioned_at
                updates["result_ref"] = transition.spec.result_ref
                updates["error"] = transition.spec.error
            operation = operation.model_copy(update={"spec": operation.spec.model_copy(update=updates)})
            ServiceFabricOperation.model_validate(operation.model_dump(mode="python", by_alias=True))
        snapshot, version = self.get(operation_id)
        if version != len(events) or snapshot != operation:
            raise CorruptOperationError("snapshot does not match replayed history")
        return operation, version
