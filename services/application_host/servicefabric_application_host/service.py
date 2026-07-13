"""Bounded local host for reviewed FastAPI application packages."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ApplicationHostError(RuntimeError):
    pass


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _atomic(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".pending")
    temporary.write_text(_json(value), encoding="utf-8")
    os.replace(temporary, path)


class LocalApplicationHost:
    """Hosts only packages using the reviewed-fastapi-v1 adapter on loopback."""

    def __init__(self, workspace: Path) -> None:
        self.root = workspace / "hosted-applications"
        self.root.mkdir(parents=True, exist_ok=True)

    def _directory(self, application_id: str) -> Path:
        if application_id != "text-utility":
            raise ApplicationHostError(f"application '{application_id}' is not installed")
        return self.root / application_id

    def _record(self, application_id: str) -> dict[str, object]:
        path = self._directory(application_id) / "application.json"
        if not path.is_file():
            raise ApplicationHostError(f"application '{application_id}' is not installed")
        return json.loads(path.read_text(encoding="utf-8"))

    def install(self, source: Path) -> dict[str, object]:
        source = source.resolve(strict=True)
        package_path = source / "servicefabric-package.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("application_id") != "text-utility" or package.get("adapter") != "reviewed-fastapi-v1":
            raise ApplicationHostError("package is not an approved AP-01A FastAPI package")
        directory = self.root / "text-utility"
        installed = not directory.exists()
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "source"
        if installed:
            shutil.copytree(source, target)
        elif package != self._record("text-utility")["package"]:
            raise ApplicationHostError("installed package differs from the reviewed package")
        record = {"application_id": "text-utility", "package": package, "state": "installed", "restart_count": 0, "request_count": 0}
        if not installed:
            record.update(self._record("text-utility"))
        _atomic(directory / "application.json", record)
        return {"application_id": "text-utility", "installed": installed, "state": record["state"]}

    def build(self, application_id: str) -> dict[str, object]:
        record = self._record(application_id)
        source = self._directory(application_id) / "source"
        digest = hashlib.sha256()
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            digest.update(path.relative_to(source).as_posix().encode())
            digest.update(path.read_bytes())
        artifact = "sha256:" + digest.hexdigest()
        record.update({"state": "built", "artifact_digest": artifact})
        _atomic(self._directory(application_id) / "application.json", record)
        return {"application_id": application_id, "revision": record["package"]["version"], "artifact_digest": artifact, "state": "built", "status": "success"}

    def list_applications(self) -> tuple[str, ...]:
        return tuple(sorted(path.name for path in self.root.iterdir() if (path / "application.json").is_file()))

    def is_installed(self, application_id: str) -> bool:
        return application_id in self.list_applications()

    @staticmethod
    def _port() -> int:
        with socket.socket() as value:
            value.bind(("127.0.0.1", 0))
            return int(value.getsockname()[1])

    @staticmethod
    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            stat = Path(f"/proc/{pid}/stat")
            return not stat.exists() or stat.read_text(encoding="utf-8").split()[2] != "Z"
        except OSError:
            return False

    def start(self, application_id: str) -> dict[str, object]:
        record = self._record(application_id)
        if "artifact_digest" not in record:
            raise ApplicationHostError("application must be built before start")
        if record.get("pid") and self._alive(int(record["pid"])):
            return self.status(application_id)
        if record.get("state") in {"stopped", "failed"}:
            record["restart_count"] = int(record.get("restart_count", 0)) + 1
        port = self._port()
        log_path = self._directory(application_id) / "application.log"
        started = time.monotonic()
        with log_path.open("ab") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log"],
                cwd=self._directory(application_id) / "source",
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        record.update({"state": "starting", "pid": process.pid, "port": port})
        _atomic(self._directory(application_id) / "application.json", record)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                record.update({"state": "failed", "exit_code": process.returncode})
                _atomic(self._directory(application_id) / "application.json", record)
                raise ApplicationHostError("application process exited before becoming healthy")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5) as response:
                    if response.status == 200:
                        record.update({"state": "running", "startup_duration_ms": round((time.monotonic() - started) * 1000, 3), "peak_memory_bytes": 0})
                        _atomic(self._directory(application_id) / "application.json", record)
                        return self.status(application_id)
            except (OSError, URLError):
                time.sleep(0.05)
        self.stop(application_id)
        raise ApplicationHostError("application health check timed out")

    def status(self, application_id: str) -> dict[str, object]:
        record = self._record(application_id)
        pid = int(record.get("pid") or 0)
        if record.get("state") in {"starting", "running"} and not self._alive(pid):
            record["state"] = "failed"
            _atomic(self._directory(application_id) / "application.json", record)
        health = "unavailable"
        if record.get("state") == "running":
            try:
                with urlopen(f"http://127.0.0.1:{record['port']}/health", timeout=1) as response:
                    health = "healthy" if response.status == 200 else "unhealthy"
            except (OSError, URLError):
                health = "unhealthy"
        return {key: record.get(key) for key in ("application_id", "state", "pid", "port", "startup_duration_ms", "restart_count", "request_count")} | {"health": health}

    def resources(self, application_id: str) -> dict[str, object]:
        record = self._record(application_id)
        pid = int(record.get("pid") or 0)
        current = 0
        if pid and self._alive(pid):
            try:
                for line in Path(f"/proc/{pid}/status").read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        current = int(line.split()[1]) * 1024
            except OSError:
                current = 0
        peak = max(int(record.get("peak_memory_bytes", 0)), current)
        record["peak_memory_bytes"] = peak
        _atomic(self._directory(application_id) / "application.json", record)
        declared = record["package"]["declared_resources"]
        return {"declared": declared, "measured": {"current_memory_bytes": current or None, "peak_memory_bytes": peak or None, "recent_cpu_percent": None, "startup_duration_ms": record.get("startup_duration_ms"), "request_count": record.get("request_count", 0), "health": self.status(application_id)["health"], "restart_count": record.get("restart_count", 0)}}

    def stop(self, application_id: str) -> dict[str, object]:
        record = self._record(application_id)
        pid = int(record.get("pid") or 0)
        if pid and self._alive(pid):
            os.kill(pid, signal.SIGTERM)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and self._alive(pid):
                time.sleep(0.05)
        record.update({"state": "stopped", "pid": None, "port": None})
        _atomic(self._directory(application_id) / "application.json", record)
        return self.status(application_id)

    def invoke(self, tool_id: str, arguments: dict[str, object]) -> dict[str, object]:
        record = self._record("text-utility")
        if self.status("text-utility")["state"] != "running":
            raise ApplicationHostError("application 'text-utility' is unavailable")
        routes = {item["tool_id"]: item["path"] for item in record["package"]["capabilities"]}
        if tool_id not in routes:
            raise ApplicationHostError(f"capability '{tool_id}' is unknown")
        body = json.dumps(arguments, sort_keys=True).encode()
        request = Request(f"http://127.0.0.1:{record['port']}{routes[tool_id]}", data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=5) as response:
                result = json.loads(response.read(1_048_577))
        except HTTPError as error:
            raise ApplicationHostError("application capability input is invalid") from error
        except (OSError, URLError) as error:
            raise ApplicationHostError("application capability gateway is unavailable") from error
        record["request_count"] = int(record.get("request_count", 0)) + 1
        _atomic(self._directory("text-utility") / "application.json", record)
        return result

    def logs(self, application_id: str, maximum_bytes: int = 16_384) -> str:
        path = self._directory(application_id) / "application.log"
        return path.read_bytes()[-maximum_bytes:].decode("utf-8", errors="replace") if path.exists() else ""
