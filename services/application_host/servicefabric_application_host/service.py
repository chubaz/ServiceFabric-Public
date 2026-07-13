"""Bounded local host for reviewed FastAPI application packages."""

from __future__ import annotations

import fcntl
import hashlib
import json
import mimetypes
import os
import resource
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder.identity import digest
from servicefabric_contracts import ApplicationArtifactManifest


MAX_RECORD_BYTES = 262_144
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_ARTIFACT_FILES = 128
MAX_LOG_BYTES = 1 * 1024 * 1024
MAX_ARGUMENT_TEXT = 100_000

_REVIEWED_PACKAGE = {
    "application_id": "text-utility",
    "version": "1.0.0",
    "framework": "fastapi",
    "adapter": "reviewed-fastapi-v1",
    "module": "app:app",
    "build": {"kind": "reviewed-python-source"},
    "start": {"adapter": "reviewed-fastapi-v1", "module": "app:app"},
    "health_path": "/health",
    "source_files": [
        {
            "path": "app.py",
            "sha256": "46375c58efbb5b6baacd817e4b0fe3f4515989c54340bf523ee0b14d20110b89",
        },
        {
            "path": "pyproject.toml",
            "sha256": "5b2cef6fcc362121b5777f03911ca65dfa3d398995e63badf39473d13697075c",
        },
    ],
    "declared_resources": {
        "memory_mib": 128,
        "cpu_cores": 0.25,
        "storage_mib": 16,
        "network": "loopback-only",
    },
    "entrypoints": ["web", "health", "capability-adapter"],
    "capabilities": [
        {"tool_id": "text.count_words", "path": "/actions/count-words"},
        {"tool_id": "text.inspect", "path": "/actions/inspect"},
    ],
}

_CAPABILITIES = {
    "text.count_words": {
        "tool_id": "text.count_words",
        "revision": "1.0.0",
        "application_id": "text-utility",
        "description": "Count words using the hosted Text Utility application.",
        "permission_id": "text-count",
        "path": "/actions/count-words",
        "effects": ("none",),
    },
    "text.inspect": {
        "tool_id": "text.inspect",
        "revision": "1.0.0",
        "application_id": "text-utility",
        "description": "Inspect text using the hosted Text Utility application.",
        "permission_id": "text-inspect",
        "path": "/actions/inspect",
        "effects": ("none",),
    },
}


class ApplicationHostError(RuntimeError):
    """Safe local application-host failure."""


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _atomic(path: Path, value: object) -> None:
    encoded = _json(value).encode("utf-8")
    if len(encoded) > MAX_RECORD_BYTES:
        raise ApplicationHostError("application state exceeds the local size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".pending-", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _limit_child_log() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_LOG_BYTES, MAX_LOG_BYTES))


class LocalApplicationHost:
    """Hosts only packages using the reviewed-fastapi-v1 adapter on loopback."""

    def __init__(
        self, workspace: Path, *, health_timeout_seconds: float = 10.0
    ) -> None:
        if health_timeout_seconds < 0.1 or health_timeout_seconds > 10.0:
            raise ValueError("health timeout must be between 0.1 and 10 seconds")
        self.root = workspace / "hosted-applications"
        self.root.mkdir(parents=True, exist_ok=True)
        self.artifacts = FileArtifactStore(workspace / "artifacts")
        self._health_timeout_seconds = health_timeout_seconds

    def _directory(self, application_id: str) -> Path:
        if application_id != "text-utility":
            raise ApplicationHostError(f"application '{application_id}' is not installed")
        return self.root / application_id

    @contextmanager
    def _lock(self, application_id: str) -> Iterator[None]:
        lock_path = self.root / f".{application_id}.lock"
        with lock_path.open("a+b") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _record(self, application_id: str) -> dict[str, object]:
        path = self._directory(application_id) / "application.json"
        if not path.is_file():
            raise ApplicationHostError(f"application '{application_id}' is not installed")
        try:
            if path.stat().st_size > MAX_RECORD_BYTES:
                raise ApplicationHostError("application state exceeds the local size limit")
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ApplicationHostError("application state is unreadable") from error
        if not isinstance(value, dict) or value.get("application_id") != application_id:
            raise ApplicationHostError("application state is invalid")
        return value

    @staticmethod
    def _validate_package(package: object) -> dict[str, object]:
        if package != _REVIEWED_PACKAGE:
            raise ApplicationHostError("package is not an approved AP-01A FastAPI package")
        return dict(package)

    @staticmethod
    def _validate_source(source: Path, package: dict[str, object]) -> None:
        declared = {
            str(item["path"]): str(item["sha256"])
            for item in package["source_files"]
        }
        actual_paths = {
            path.relative_to(source).as_posix()
            for path in source.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
            and path.name != "servicefabric-package.json"
        }
        if actual_paths != set(declared):
            raise ApplicationHostError("package source files do not match the reviewed manifest")
        for relative, expected in declared.items():
            path = source / relative
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ApplicationHostError("package source failed reviewed digest verification")

    def install(self, source: Path) -> dict[str, object]:
        try:
            source = source.resolve(strict=True)
        except OSError as error:
            raise ApplicationHostError("package source is unavailable") from error
        if not source.is_dir():
            raise ApplicationHostError("package source must be a directory")
        try:
            package = self._validate_package(
                json.loads((source / "servicefabric-package.json").read_text(encoding="utf-8"))
            )
            self._validate_source(source, package)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ApplicationHostError("package manifest is unreadable") from error
        with self._lock("text-utility"):
            directory = self.root / "text-utility"
            installed = not directory.exists()
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / "source"
            if installed:
                shutil.copytree(
                    source,
                    target,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
                record: dict[str, object] = {
                    "application_id": "text-utility",
                    "package": package,
                    "state": "installed",
                    "restart_count": 0,
                    "request_count": 0,
                }
            else:
                record = self._record("text-utility")
                if package != record.get("package"):
                    raise ApplicationHostError("installed package differs from the reviewed package")
            _atomic(directory / "application.json", record)
        return {
            "application_id": "text-utility",
            "installed": installed,
            "state": record["state"],
        }

    def build(self, application_id: str) -> dict[str, object]:
        with self._lock(application_id):
            record = self._record(application_id)
            if (
                record.get("state") == "starting" and self._same_process(record)
            ) or (
                record.get("state") == "running" and self._owned_process(record)
            ):
                raise ApplicationHostError("running application must be stopped before rebuild")
            source = self._directory(application_id) / "source"
            self._validate_source(source, record["package"])
            paths = sorted(
                item
                for item in source.rglob("*")
                if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
            )
            if len(paths) > MAX_ARTIFACT_FILES:
                raise ApplicationHostError("application artifact contains too many files")
            files = []
            total_size = 0
            for path in paths:
                content = path.read_bytes()
                total_size += len(content)
                if total_size > MAX_ARTIFACT_BYTES:
                    raise ApplicationHostError("application artifact exceeds the local size limit")
                relative = path.relative_to(source).as_posix()
                files.append(
                    {
                        "path": relative,
                        "content_digest": "sha256:" + hashlib.sha256(content).hexdigest(),
                        "media_type": mimetypes.guess_type(relative)[0]
                        or "application/octet-stream",
                        "size_bytes": len(content),
                    }
                )
            source_digest = digest(files)
            build_spec_digest = digest(record["package"]["build"])
            stable = {
                "application_id": application_id,
                "application_revision": record["package"]["version"],
                "builder_id": "reviewed-fastapi-source-builder",
                "builder_revision": "1.0.0",
                "source_digest": source_digest,
                "build_spec_digest": build_spec_digest,
                "files": files,
                "entry_document": "app.py",
                "total_size_bytes": total_size,
                "reproducibility": "reproducible",
            }
            artifact = digest(stable)
            artifact_id = "artifact." + artifact[7:39]
            manifest = ApplicationArtifactManifest.model_validate(
                {
                    "apiVersion": "servicefabric.ai/v1alpha1",
                    "kind": "ApplicationArtifactManifest",
                    "metadata": {
                        "id": artifact_id,
                        "name": "Text Utility 1.0.0",
                        "description": "Immutable reviewed FastAPI source artifact.",
                        "owner_ref": {"kind": "service", "id": "application-host"},
                    },
                    "spec": {
                        **stable,
                        "artifact_id": artifact_id,
                        "artifact_digest": artifact,
                        "provenance": {
                            "source_manifest_ref": "text-utility-source",
                            "source_digest": source_digest,
                            "build_spec_digest": build_spec_digest,
                            "builder_id": "reviewed-fastapi-source-builder",
                            "builder_revision": "1.0.0",
                        },
                    },
                }
            )
            self.artifacts.put_artifact(manifest, source)
            record.update(
                {"state": "built", "artifact_digest": artifact, "artifact_id": artifact_id}
            )
            _atomic(self._directory(application_id) / "application.json", record)
            return {
                "application_id": application_id,
                "revision": record["package"]["version"],
                "artifact_digest": artifact,
                "state": "built",
                "status": "success",
            }

    def list_applications(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                path.name
                for path in self.root.iterdir()
                if (path / "application.json").is_file()
            )
        )

    def is_installed(self, application_id: str) -> bool:
        return application_id in self.list_applications()

    def capabilities(self) -> tuple[dict[str, object], ...]:
        if not self.is_installed("text-utility"):
            return ()
        record = self._record("text-utility")
        self._validate_package(record.get("package"))
        return tuple(dict(_CAPABILITIES[key]) for key in sorted(_CAPABILITIES))

    def describe_capability(self, tool_id: str) -> dict[str, object]:
        available = {item["tool_id"]: item for item in self.capabilities()}
        if tool_id not in available:
            raise ApplicationHostError(f"capability '{tool_id}' is unknown")
        return dict(available[tool_id])

    @staticmethod
    def _port() -> int:
        with socket.socket() as value:
            value.bind(("127.0.0.1", 0))
            return int(value.getsockname()[1])

    @staticmethod
    def _process_fields(pid: int) -> tuple[str, int, int] | None:
        try:
            text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
            fields = text[text.rfind(")") + 2 :].split()
            return fields[0], int(fields[19]), int(fields[11]) + int(fields[12])
        except (OSError, ValueError, IndexError):
            return None

    @classmethod
    def _alive(cls, pid: int) -> bool:
        fields = cls._process_fields(pid)
        return bool(fields and fields[0] != "Z")

    @classmethod
    def _same_process(cls, record: dict[str, object]) -> bool:
        pid = int(record.get("pid") or 0)
        expected_start = record.get("process_start_ticks")
        fields = cls._process_fields(pid)
        return bool(fields and fields[0] != "Z" and fields[1] == expected_start)

    @classmethod
    def _owned_process(cls, record: dict[str, object]) -> bool:
        pid = int(record.get("pid") or 0)
        if not cls._same_process(record):
            return False
        try:
            command = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        except OSError:
            return False
        expected = [
            os.fsencode(sys.executable),
            b"-m",
            b"uvicorn",
            b"app:app",
            b"--host",
            b"127.0.0.1",
            b"--port",
            str(record.get("port")).encode("ascii"),
            b"--no-access-log",
        ]
        return command[: len(expected)] == expected

    def _health(self, record: dict[str, object]) -> str:
        if record.get("state") != "running" or not self._owned_process(record):
            return "unavailable"
        try:
            with urlopen(
                f"http://127.0.0.1:{record['port']}/health", timeout=1
            ) as response:
                return "healthy" if response.status == 200 else "unhealthy"
        except (OSError, URLError):
            return "unhealthy"

    def _status_value(self, record: dict[str, object]) -> dict[str, object]:
        return {
            key: record.get(key)
            for key in (
                "application_id",
                "state",
                "pid",
                "port",
                "startup_duration_ms",
                "restart_count",
                "request_count",
            )
        } | {"health": self._health(record)}

    def start(self, application_id: str) -> dict[str, object]:
        with self._lock(application_id):
            record = self._record(application_id)
            if "artifact_digest" not in record:
                raise ApplicationHostError("application must be built before start")
            if (
                record.get("state") == "starting" and self._same_process(record)
            ) or (
                record.get("state") == "running" and self._owned_process(record)
            ):
                return self._status_value(record)
            if record.get("state") in {"stopped", "failed"}:
                record["restart_count"] = int(record.get("restart_count", 0)) + 1
            port = self._port()
            artifact = str(record["artifact_digest"])
            verification = self.artifacts.verify_artifact(artifact)
            if not verification.valid:
                raise ApplicationHostError("application artifact failed integrity verification")
            manifest = self.artifacts.get_manifest(artifact)
            if (
                len(manifest.spec.files) > MAX_ARTIFACT_FILES
                or manifest.spec.total_size_bytes > MAX_ARTIFACT_BYTES
            ):
                raise ApplicationHostError("application artifact exceeds host limits")
            runtime_root = self._directory(application_id) / "runtime"
            shutil.rmtree(runtime_root, ignore_errors=True)
            runtime_root.mkdir()
            for item in manifest.spec.files:
                target = runtime_root / item.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.artifacts.open_file(artifact, item.path))
            log_path = self._directory(application_id) / "application.log"
            log_path.write_bytes(b"")
            started = time.monotonic()
            with log_path.open("ab") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                        "--no-access-log",
                    ],
                    cwd=runtime_root,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    preexec_fn=_limit_child_log,
                )
            process_fields = self._process_fields(process.pid)
            if not process_fields:
                process.terminate()
                raise ApplicationHostError("application process identity is unavailable")
            record.update(
                {
                    "state": "starting",
                    "pid": process.pid,
                    "port": port,
                    "process_start_ticks": process_fields[1],
                }
            )
            _atomic(self._directory(application_id) / "application.json", record)
        deadline = time.monotonic() + self._health_timeout_seconds
        while time.monotonic() < deadline:
            if process.poll() is not None:
                with self._lock(application_id):
                    current = self._record(application_id)
                    if current.get("state") != "stopped":
                        current.update({"state": "failed", "exit_code": process.returncode})
                        _atomic(
                            self._directory(application_id) / "application.json", current
                        )
                raise ApplicationHostError(
                    "application process exited before becoming healthy"
                )
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5) as response:
                    if response.status == 200:
                        with self._lock(application_id):
                            current = self._record(application_id)
                            if (
                                current.get("pid") != process.pid
                                or current.get("state") != "starting"
                                or not self._owned_process(current)
                            ):
                                raise ApplicationHostError(
                                    "application startup was superseded"
                                )
                            current.update(
                                {
                                    "state": "running",
                                    "startup_duration_ms": round(
                                        (time.monotonic() - started) * 1000, 3
                                    ),
                                    "peak_memory_bytes": None,
                                }
                            )
                            _atomic(
                                self._directory(application_id) / "application.json",
                                current,
                            )
                            return self._status_value(current)
            except (OSError, URLError):
                time.sleep(0.05)
        with self._lock(application_id):
            current = self._record(application_id)
            if current.get("pid") == process.pid:
                self._terminate_owned(current)
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
                current["state"] = "failed"
                _atomic(self._directory(application_id) / "application.json", current)
        raise ApplicationHostError("application health check timed out")

    def status(self, application_id: str) -> dict[str, object]:
        with self._lock(application_id):
            record = self._record(application_id)
            alive = (
                self._same_process(record)
                if record.get("state") == "starting"
                else self._owned_process(record)
            )
            if record.get("state") in {"starting", "running"} and not alive:
                record["state"] = "failed"
                _atomic(self._directory(application_id) / "application.json", record)
            return self._status_value(record)

    def resources(self, application_id: str) -> dict[str, object]:
        with self._lock(application_id):
            record = self._record(application_id)
            pid = int(record.get("pid") or 0)
            current = None
            if self._owned_process(record):
                try:
                    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
                        if line.startswith("VmRSS:"):
                            current = int(line.split()[1]) * 1024
                except (OSError, ValueError, IndexError):
                    current = None
            previous_peak = record.get("peak_memory_bytes")
            peak = max(
                value for value in (previous_peak, current) if isinstance(value, int)
            ) if any(isinstance(value, int) for value in (previous_peak, current)) else None
            cpu = self._cpu_percent(pid) if self._owned_process(record) else None
            record["peak_memory_bytes"] = peak
            _atomic(self._directory(application_id) / "application.json", record)
            declared = record["package"]["declared_resources"]
            return {
                "declared": declared,
                "measured": {
                    "current_memory_bytes": current,
                    "peak_memory_bytes": peak,
                    "recent_cpu_percent": cpu,
                    "startup_duration_ms": record.get("startup_duration_ms"),
                    "request_count": record.get("request_count", 0),
                    "health": self._health(record),
                    "restart_count": record.get("restart_count", 0),
                    "process_scope": "managed-process-group-leader",
                },
            }

    @classmethod
    def _cpu_percent(cls, pid: int) -> float | None:
        try:
            clock_ticks = os.sysconf("SC_CLK_TCK")
            before_fields = cls._process_fields(pid)
            if not before_fields:
                return None
            started = time.monotonic()
            time.sleep(0.05)
            after_fields = cls._process_fields(pid)
            if not after_fields or after_fields[1] != before_fields[1]:
                return None
            return round(
                ((after_fields[2] - before_fields[2]) / clock_ticks)
                / (time.monotonic() - started)
                * 100,
                3,
            )
        except (OSError, ValueError, IndexError):
            return None

    def _terminate_owned(self, record: dict[str, object]) -> None:
        if not self._owned_process(record):
            return
        pid = int(record["pid"])
        os.killpg(pid, signal.SIGTERM)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and self._owned_process(record):
            time.sleep(0.05)
        if self._owned_process(record):
            os.killpg(pid, signal.SIGKILL)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and self._owned_process(record):
                time.sleep(0.05)
        if self._owned_process(record):
            raise ApplicationHostError("application process did not stop within host limits")

    def stop(self, application_id: str) -> dict[str, object]:
        with self._lock(application_id):
            record = self._record(application_id)
            if record.get("pid") and not self._owned_process(record):
                if record.get("state") in {"starting", "running"}:
                    record["state"] = "failed"
                record.update({"pid": None, "port": None, "process_start_ticks": None})
                _atomic(self._directory(application_id) / "application.json", record)
                return self._status_value(record)
            self._terminate_owned(record)
            record.update(
                {
                    "state": "stopped",
                    "pid": None,
                    "port": None,
                    "process_start_ticks": None,
                }
            )
            _atomic(self._directory(application_id) / "application.json", record)
            return self._status_value(record)

    @staticmethod
    def _validate_arguments(arguments: object) -> dict[str, object]:
        if not isinstance(arguments, dict) or set(arguments) != {"text"}:
            raise ApplicationHostError("application capability input is invalid")
        text = arguments.get("text")
        if not isinstance(text, str) or not text or len(text) > MAX_ARGUMENT_TEXT:
            raise ApplicationHostError("application capability input is invalid")
        return arguments

    def invoke(self, tool_id: str, arguments: dict[str, object]) -> dict[str, object]:
        descriptor = self.describe_capability(tool_id)
        arguments = self._validate_arguments(arguments)
        with self._lock("text-utility"):
            record = self._record("text-utility")
            if record.get("state") != "running" or not self._owned_process(record):
                raise ApplicationHostError("application 'text-utility' is unavailable")
            port = int(record["port"])
        body = json.dumps(arguments, sort_keys=True).encode()
        request = Request(
            f"http://127.0.0.1:{port}{descriptor['path']}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                encoded = response.read(1_048_577)
                if len(encoded) > 1_048_576:
                    raise ApplicationHostError("application capability response exceeds limits")
                result = json.loads(encoded)
        except HTTPError as error:
            raise ApplicationHostError("application capability input is invalid") from error
        except (OSError, URLError) as error:
            raise ApplicationHostError("application capability gateway is unavailable") from error
        except json.JSONDecodeError as error:
            raise ApplicationHostError("application capability returned an invalid response") from error
        with self._lock("text-utility"):
            record = self._record("text-utility")
            record["request_count"] = int(record.get("request_count", 0)) + 1
            _atomic(self._directory("text-utility") / "application.json", record)
        return result

    def logs(self, application_id: str, maximum_bytes: int = 16_384) -> str:
        if maximum_bytes < 0 or maximum_bytes > MAX_LOG_BYTES:
            raise ApplicationHostError("requested log size exceeds host limits")
        path = self._directory(application_id) / "application.log"
        return (
            path.read_bytes()[-maximum_bytes:].decode("utf-8", errors="replace")
            if path.exists()
            else ""
        )
