"""ManagedProcessController coordinating dynamic subprocess lifecycles."""

from __future__ import annotations

import hashlib
import os
import signal
import sys
import time
from pathlib import Path
from typing import Callable

from servicefabric_workspace import WorkspaceLayout
from servicefabric_workspace.locking import file_lock
from servicefabric_process_runtime.errors import ProcessRuntimeError, ProcessStartError
from servicefabric_process_runtime.identity import (
    get_process_fields,
    is_alive,
    is_owned_process,
    is_same_process,
)
from servicefabric_process_runtime.models import (
    ProcessIdentity,
    ProcessResourceSnapshot,
    ProcessStatus,
    ResolvedProcessPlan,
)
from servicefabric_process_runtime.records import ModuleRuntimeRecord, ModuleRuntimeStore


class ManagedProcessController:
    """Manages the full subprocess lifecycle including launch, health, and stop."""

    def __init__(self, workspace: WorkspaceLayout):
        self.workspace = workspace
        self.store = ModuleRuntimeStore(workspace)

    def start(self, plan: ResolvedProcessPlan, on_start: Callable[[int, int], None] | None = None) -> ProcessStatus:
        """Launches a managed loopback process according to the resolved plan.

        Idempotently verifies if process already exists, starts process group leader,

        polls readiness health targets, and cleans up on startup failures.

        Raises:
            ProcessStartError: If process fails to start or health check times out.
        """
        lock_path = self.store.get_lock_path(plan.application_id, plan.module_id)

        # 1. Acquire lock to launch process safely
        with file_lock(lock_path):
            existing = self.store.load(plan.application_id, plan.module_id)
            if existing and existing.state in {"starting", "running"}:
                # Verify if process is indeed alive and matches expected command line
                if existing.pid and is_owned_process(
                    existing.pid,
                    existing.process_start_ticks or 0,
                    plan.executable,
                    list(plan.arguments),
                ):
                    return self._status_value(existing)
                else:
                    # Dead or stale process, transition to failed
                    existing.state = "failed"
                    existing.pid = None
                    existing.port = None
                    self.store.save(existing)

            # Launch process group
            t0 = time.monotonic()
            plan.log_path.parent.mkdir(parents=True, exist_ok=True)
            log_file = open(plan.log_path, "wb")

            try:
                import subprocess
                process = subprocess.Popen(
                    [str(plan.executable)] + list(plan.arguments),
                    cwd=str(plan.working_directory),
                    env=plan.environment,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid,  # Background process group leader
                )
            except Exception as exc:
                log_file.close()
                raise ProcessStartError(f"Failed to launch subprocess: {exc}") from exc

            # Give OS a brief moment to initialize the process fields
            time.sleep(0.01)
            fields = get_process_fields(process.pid)
            if not fields:
                process.wait()
                log_file.close()
                raise ProcessStartError("Subprocess failed to launch or exited immediately.")

            start_ticks = fields[1]
            cmd_str = " ".join([str(plan.executable)] + list(plan.arguments))
            expected_command_digest = "sha256:" + hashlib.sha256(cmd_str.encode("utf-8")).hexdigest()

            # Save the record in "starting" state first
            start_record = ModuleRuntimeRecord(
                application_id=plan.application_id,
                module_id=plan.module_id,
                adapter_id=plan.adapter_id,
                state="starting",
                pid=process.pid,
                process_start_ticks=start_ticks,
                port=plan.port,
                health="unavailable",
                restart_count=(existing.restart_count if existing else 0),
                startup_duration_ms=None,
                peak_memory_bytes=existing.peak_memory_bytes if existing else None,
            )
            self.store.save(start_record)

            # Invoke callback immediately upon launch
            if on_start is not None:
                try:
                    on_start(process.pid, start_ticks)
                except Exception:
                    pass

        # 2. Release lock and poll startup health probe
        health = "unavailable"
        state = "starting"
        startup_duration_ms = None

        if plan.health_target.url:
            from servicefabric_process_runtime.health import poll_health_http
            success = poll_health_http(
                plan.health_target.url, plan.health_target.timeout_seconds
            )
            
            # Acquire lock again to update the final status safely
            with file_lock(lock_path):
                current = self.store.load(plan.application_id, plan.module_id)
                if not current or current.pid != process.pid or current.state != "starting":
                    log_file.close()
                    raise ProcessStartError("Subprocess startup was superseded or stopped.")
                
                if success:
                    health = "healthy"
                    state = "running"
                    startup_duration_ms = (time.monotonic() - t0) * 1000
                    
                    new_record = ModuleRuntimeRecord(
                        application_id=plan.application_id,
                        module_id=plan.module_id,
                        adapter_id=plan.adapter_id,
                        state=state,
                        pid=process.pid,
                        process_start_ticks=start_ticks,
                        port=plan.port,
                        health=health,
                        restart_count=current.restart_count,
                        startup_duration_ms=startup_duration_ms,
                        peak_memory_bytes=current.peak_memory_bytes,
                    )
                    self.store.save(new_record)
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    except OSError:
                        pass
                    log_file.close()

                    fail_record = ModuleRuntimeRecord(
                        application_id=plan.application_id,
                        module_id=plan.module_id,
                        adapter_id=plan.adapter_id,
                        state="failed",
                        pid=None,
                        port=None,
                        health="unavailable",
                        restart_count=current.restart_count,
                    )
                    self.store.save(fail_record)
                    raise ProcessStartError("Subprocess health check timed out.")
        else:
            time.sleep(0.1)
            with file_lock(lock_path):
                current = self.store.load(plan.application_id, plan.module_id)
                if not current or current.pid != process.pid or current.state != "starting":
                    log_file.close()
                    raise ProcessStartError("Subprocess startup was superseded.")
                
                if is_alive(process.pid):
                    state = "running"
                    health = "healthy"
                    startup_duration_ms = (time.monotonic() - t0) * 1000
                    
                    new_record = ModuleRuntimeRecord(
                        application_id=plan.application_id,
                        module_id=plan.module_id,
                        adapter_id=plan.adapter_id,
                        state=state,
                        pid=process.pid,
                        process_start_ticks=start_ticks,
                        port=plan.port,
                        health=health,
                        restart_count=current.restart_count,
                        startup_duration_ms=startup_duration_ms,
                        peak_memory_bytes=current.peak_memory_bytes,
                    )
                    self.store.save(new_record)
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    except OSError:
                        pass
                    log_file.close()
                    
                    fail_record = ModuleRuntimeRecord(
                        application_id=plan.application_id,
                        module_id=plan.module_id,
                        adapter_id=plan.adapter_id,
                        state="failed",
                        pid=None,
                        port=None,
                        health="unavailable",
                        restart_count=current.restart_count,
                    )
                    self.store.save(fail_record)
                    raise ProcessStartError("Subprocess exited immediately.")

        log_file.close()
        return self._status_value(new_record)

    def status(self, application_id: str, module_id: str) -> ProcessStatus:
        """Retrieves the status of a managed process, dynamically validating its identity."""
        lock_path = self.store.get_lock_path(application_id, module_id)

        with file_lock(lock_path):
            record = self.store.load(application_id, module_id)
            if not record:
                return ProcessStatus(
                    state="stopped",
                    identity=None,
                    port=None,
                    health="unavailable",
                    startup_duration_ms=None,
                )

            if record.pid:
                if is_same_process(record.pid, record.process_start_ticks or 0):
                    health = "unavailable"
                    if record.state == "running":
                        health = self._fast_health_check(record.port)
                    record.health = health
                    self.store.save(record)
                    return self._status_value(record)
                else:
                    # Dead or stale process detected, transition to failed
                    record.state = "failed"
                    record.pid = None
                    record.port = None
                    record.process_start_ticks = None
                    record.health = "unavailable"
                    self.store.save(record)
                    return self._status_value(record)

            return self._status_value(record)

    def resources(self, application_id: str, module_id: str) -> ProcessResourceSnapshot:
        """Samples the memory (VmRSS) and CPU of the process over a 50ms interval."""
        lock_path = self.store.get_lock_path(application_id, module_id)

        with file_lock(lock_path):
            record = self.store.load(application_id, module_id)
            if not record or not record.pid:
                return ProcessResourceSnapshot(
                    current_memory_bytes=None,
                    peak_memory_bytes=record.peak_memory_bytes if record else None,
                    recent_cpu_percent=None,
                )

            if not is_same_process(record.pid, record.process_start_ticks or 0):
                return ProcessResourceSnapshot(
                    current_memory_bytes=None,
                    peak_memory_bytes=record.peak_memory_bytes,
                    recent_cpu_percent=None,
                )

            from servicefabric_process_runtime.resources import (
                measure_cpu_percent,
                measure_memory_bytes,
            )

            mem = measure_memory_bytes(record.pid)
            cpu = measure_cpu_percent(record.pid)

            previous_peak = record.peak_memory_bytes
            peak = (
                max(value for value in (previous_peak, mem) if isinstance(value, int))
                if any(isinstance(value, int) for value in (previous_peak, mem))
                else None
            )

            record.peak_memory_bytes = peak
            self.store.save(record)

            return ProcessResourceSnapshot(
                current_memory_bytes=mem,
                peak_memory_bytes=peak,
                recent_cpu_percent=cpu,
            )

    def logs(self, application_id: str, module_id: str, maximum_bytes: int) -> str:
        """Reads the bounded trailing bytes of the module's stdout/stderr log file."""
        record = self.store.load(application_id, module_id)
        if not record:
            return ""

        log_path = (
            self.workspace.logs / "applications" / application_id / f"{module_id}.log"
        )
        if not log_path.is_file():
            return ""

        try:
            size = log_path.stat().st_size
            with log_path.open("r", encoding="utf-8", errors="ignore") as handle:
                if size > maximum_bytes:
                    handle.seek(size - maximum_bytes)
                return handle.read()
        except Exception:
            return ""

    def stop(self, application_id: str, module_id: str) -> ProcessStatus:
        """Terminates the process group leader using SIGTERM, escalating to SIGKILL on timeout.

        This operation is fully thread-safe and idempotent.
        """
        lock_path = self.store.get_lock_path(application_id, module_id)

        with file_lock(lock_path):
            record = self.store.load(application_id, module_id)
            if not record:
                return ProcessStatus(
                    state="stopped",
                    identity=None,
                    port=None,
                    health="unavailable",
                    startup_duration_ms=None,
                )

            if not record.pid:
                record.state = "stopped"
                record.health = "unavailable"
                self.store.save(record)
                return self._status_value(record)

            pid = record.pid
            ticks = record.process_start_ticks or 0

            if not is_same_process(pid, ticks):
                # Stale process already dead or reuse, clean up record
                if record.state in {"starting", "running"}:
                    record.state = "failed"
                else:
                    record.state = "stopped"
                record.pid = None
                record.port = None
                record.process_start_ticks = None
                record.health = "unavailable"
                self.store.save(record)
                return self._status_value(record)

            # Signal termination to process group
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError:
                pass

            deadline = time.monotonic() + 5.0
            stopped = False
            while time.monotonic() < deadline:
                if not is_same_process(pid, ticks):
                    stopped = True
                    break
                time.sleep(0.05)

            if not stopped:
                # Escalation to SIGKILL
                try:
                    os.killpg(pid, signal.SIGKILL)
                except OSError:
                    pass

                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline:
                    if not is_same_process(pid, ticks):
                        stopped = True
                        break
                    time.sleep(0.05)

            if not stopped:
                raise ProcessRuntimeError(
                    f"Subprocess '{module_id}' PID {pid} failed to stop within host limits."
                )

            # Save clean stopped record
            record.state = "stopped"
            record.pid = None
            record.port = None
            record.process_start_ticks = None
            record.health = "unavailable"
            self.store.save(record)

            return self._status_value(record)

    def _fast_health_check(self, port: int | None) -> str:
        if port is None:
            return "unavailable"
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.1) as response:
                if response.status == 200:
                    return "healthy"
                return "unhealthy"
        except Exception:
            return "unhealthy"

    def _status_value(self, record: ModuleRuntimeRecord) -> ProcessStatus:
        identity = None
        if record.pid and record.process_start_ticks:
            identity = ProcessIdentity(
                pid=record.pid,
                process_start_ticks=record.process_start_ticks,
                expected_command_digest="unresolved",
            )
        return ProcessStatus(
            state=record.state,
            identity=identity,
            port=record.port,
            health=record.health,
            startup_duration_ms=record.startup_duration_ms,
        )
