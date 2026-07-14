"""Durable application-local resource bindings.

This module deliberately owns resource preparation only.  Starting processes and
projecting the resulting environment into them remains the supervisor's job.
"""

from __future__ import annotations

import json
import os
import socket
import tempfile
from collections.abc import Iterable
from pathlib import Path

from servicefabric_resource_bindings.errors import InvalidResourceBinding
from servicefabric_resource_bindings.identifiers import environment_key_for, validate_resource_id
from servicefabric_resource_bindings.models import BoundResource, ResourceBindingPlan, ResourceBindingRequest

_SQLITE_TYPES = {"sqlite", "relational-database"}
_FILESYSTEM_TYPES = {"filesystem", "file-system"}
_LOOPBACK_TYPES = {"loopback", "http-endpoint", "web-endpoint"}


class ApplicationLocalBindings:
    """Resolve and persist application-scoped local development resources.

    ``state_directory`` is a private, application-specific directory supplied by
    the caller.  This keeps bindings for separate applications physically
    isolated while allowing repeated prepare operations to be idempotent.
    """

    def __init__(self, application_id: str, state_directory: Path) -> None:
        self.application_id = validate_resource_id(application_id, "application id")
        self._root = Path(state_directory).resolve()
        self._bindings_file = self._root / "resolved-bindings.json"

    def plan(
        self, module_id: str, requests: Iterable[ResourceBindingRequest]
    ) -> ResourceBindingPlan:
        """Resolve requests and return launch-safe environment values."""

        return ResourceBindingPlan(module_id=module_id, bindings=self.resolve(requests))

    def resolve(
        self, requests: Iterable[ResourceBindingRequest]
    ) -> tuple[BoundResource, ...]:
        """Prepare requested resources, reusing active persisted allocations."""

        requested = tuple(requests)
        for request in requested:
            validate_resource_id(request.id)
            if request.scope != "application":
                raise InvalidResourceBinding("local bindings require application scope")

        state = self._load_state()
        bindings = state["bindings"]
        resolved: list[BoundResource] = []
        changed = False
        for request in requested:
            current = bindings.get(request.id)
            if current is not None:
                if current["type"] != request.type:
                    raise InvalidResourceBinding(
                        f"persisted binding '{request.id}' has type '{current['type']}', "
                        f"not '{request.type}'"
                    )
                if current["status"] == "active":
                    resolved.append(_bound_from_record(current))
                    continue

            record = self._create_record(request)
            bindings[request.id] = record
            resolved.append(_bound_from_record(record))
            changed = True

        if changed:
            self._write_state(state)
        return tuple(resolved)

    def release(self) -> None:
        """Release volatile allocations while preserving SQLite and filesystem data."""

        state = self._load_state()
        changed = False
        for record in state["bindings"].values():
            if record["kind"] == "loopback" and record["status"] == "active":
                record["status"] = "released"
                changed = True
        if changed:
            self._write_state(state)

    def _create_record(self, request: ResourceBindingRequest) -> dict[str, object]:
        kind = _kind_for(request.type)
        if kind == "sqlite":
            data_path = self._managed_path("sqlite", f"{request.id}.sqlite3")
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.touch(exist_ok=True)
            environment = {
                environment_key_for(request.id, "URL"): f"sqlite:///{data_path}",
                environment_key_for(request.id, "PATH"): str(data_path),
            }
        elif kind == "filesystem":
            data_path = self._managed_path("filesystem", request.id)
            data_path.mkdir(parents=True, exist_ok=True)
            environment = {environment_key_for(request.id, "PATH"): str(data_path)}
        else:
            port = _allocate_loopback_port()
            environment = {
                environment_key_for(request.id, "HOST"): "127.0.0.1",
                environment_key_for(request.id, "PORT"): str(port),
                environment_key_for(request.id, "URL"): f"http://127.0.0.1:{port}",
            }

        return {
            "id": request.id,
            "type": request.type,
            "scope": request.scope,
            "kind": kind,
            "status": "active",
            "environment": dict(sorted(environment.items())),
        }

    def _managed_path(self, directory: str, name: str) -> Path:
        root = self._root / directory
        candidate = (root / name).resolve(strict=False)
        resolved_root = root.resolve(strict=False)
        if not candidate.is_relative_to(resolved_root):
            raise InvalidResourceBinding("binding path escapes application state")
        return candidate

    def _load_state(self) -> dict[str, object]:
        if not self._bindings_file.exists():
            return {"format": 1, "application_id": self.application_id, "bindings": {}}
        if self._bindings_file.is_symlink():
            raise InvalidResourceBinding("resolved bindings file must not be a symlink")
        try:
            state = json.loads(self._bindings_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InvalidResourceBinding("resolved bindings file is unreadable") from exc
        if (
            state.get("format") != 1
            or state.get("application_id") != self.application_id
            or not isinstance(state.get("bindings"), dict)
        ):
            raise InvalidResourceBinding("resolved bindings file does not match this application")
        return state

    def _write_state(self, state: dict[str, object]) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self._root, prefix=".resolved-bindings-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._bindings_file)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise


def _kind_for(resource_type: str) -> str:
    if resource_type in _SQLITE_TYPES:
        return "sqlite"
    if resource_type in _FILESYSTEM_TYPES:
        return "filesystem"
    if resource_type in _LOOPBACK_TYPES:
        return "loopback"
    raise InvalidResourceBinding(f"unsupported application-local resource type '{resource_type}'")


def _bound_from_record(record: dict[str, object]) -> BoundResource:
    return BoundResource(
        id=str(record["id"]), type=str(record["type"]), scope=str(record["scope"]),
        provider_id="application-local", environment=dict(record["environment"]),
        secret_refs={}, readiness="ready",
    )


def _allocate_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])
