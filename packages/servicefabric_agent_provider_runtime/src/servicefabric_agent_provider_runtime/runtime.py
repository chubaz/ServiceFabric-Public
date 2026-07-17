"""Provider subprocess lifecycle management.

Adapters own provider-specific command construction and event/result translation.
This module only supplies the bounded process lifecycle around that public seam.
"""
from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable
from threading import RLock

from servicefabric_agent_provider_contracts import (
    ExecutableHarnessAdapter,
    ProviderEvent,
    ProviderExecutionRequest,
    ProviderExecutionResult,
    ProviderRunHandle,
    ProviderUsage,
)


class ProviderRuntimeError(RuntimeError):
    """Raised when a request cannot be launched by this runtime."""


class ProviderRuntime:
    """Run registered provider adapters without a shell or dynamic imports.

    Each invocation is synchronous.  ``cancel`` is intentionally exposed for
    callers running ``execute`` in their own worker thread.
    """

    def __init__(self, adapters: Iterable[ExecutableHarnessAdapter] = ()) -> None:
        values = tuple(adapters)
        identifiers = tuple(adapter.provider_id for adapter in values)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("provider adapter IDs must be unique")
        self._adapters = {adapter.provider_id: adapter for adapter in values}
        self._processes: dict[str, subprocess.Popen[str]] = {}
        self._lock = RLock()

    def execute(self, request: ProviderExecutionRequest) -> ProviderExecutionResult:
        """Execute one explicit adapter command within the request timeout."""
        adapter = self._adapter_for(request.provider_id)
        argv = adapter.build_argv(request)
        if not argv or any(not isinstance(value, str) or not value for value in argv):
            raise ProviderRuntimeError("provider adapter must return a non-empty argv tuple")

        environment = self._environment_for(request)
        try:
            process = subprocess.Popen(
                argv,
                cwd=request.repository,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
        except OSError as error:
            raise ProviderRuntimeError(f"could not launch provider {request.provider_id}") from error

        handle = ProviderRunHandle(
            provider_id=request.provider_id,
            run_id=request.run_id,
            task_id=request.task_id,
            process_id=process.pid,
            state="running",
        )
        with self._lock:
            if request.run_id in self._processes:
                process.terminate()
                process.wait()
                raise ProviderRuntimeError(f"provider run is already active: {request.run_id}")
            self._processes[request.run_id] = process

        try:
            stdout, _stderr = process.communicate(timeout=request.timeout_seconds)
            events = self._parse_events(adapter, stdout)
            return adapter.recover_result(
                handle.model_copy(update={"state": "success" if process.returncode == 0 else "failed"}),
                events,
                ProviderUsage(),
                exit_code=process.returncode,
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, _stderr = process.communicate()
            events = self._parse_events(adapter, stdout)
            result = adapter.recover_result(
                handle.model_copy(update={"state": "failed"}),
                events,
                ProviderUsage(),
                exit_code=None,
            )
            return result.model_copy(update={"status": "timeout"})
        finally:
            with self._lock:
                self._processes.pop(request.run_id, None)

    def cancel(self, run_id: str) -> bool:
        """Terminate an active run and report whether it was known to the runtime."""
        with self._lock:
            process = self._processes.get(run_id)
        if process is None or process.poll() is not None:
            return False
        process.terminate()
        return True

    def active_run_ids(self) -> tuple[str, ...]:
        """Return a stable snapshot of currently executing canonical run IDs."""
        with self._lock:
            return tuple(sorted(self._processes))

    def _adapter_for(self, provider_id: str) -> ExecutableHarnessAdapter:
        try:
            return self._adapters[provider_id]
        except KeyError as error:
            raise ProviderRuntimeError(f"provider adapter is unavailable: {provider_id}") from error

    @staticmethod
    def _environment_for(request: ProviderExecutionRequest) -> dict[str, str]:
        """Forward only explicitly named ambient variables, never contract values."""
        return {
            name: os.environ[name]
            for name in request.environment_names
            if name in os.environ
        }

    @staticmethod
    def _parse_events(
        adapter: ExecutableHarnessAdapter, stdout: str,
    ) -> tuple[ProviderEvent, ...]:
        events: list[ProviderEvent] = []
        for raw_event in stdout.splitlines():
            event = adapter.parse_event(raw_event, len(events))
            if event is not None:
                events.append(event)
        return tuple(events)
