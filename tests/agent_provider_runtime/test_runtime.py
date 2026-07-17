from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from threading import Thread
from time import sleep
import unittest

ROOT = Path(__file__).resolve().parents[2]
for source in reversed((
    ROOT / "packages" / "servicefabric_contracts" / "src",
    ROOT / "packages" / "servicefabric_agentic_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_runtime" / "src",
)):
    sys.path.insert(0, str(source))

from servicefabric_agent_provider_contracts import (
    ProviderEvent, ProviderExecutionRequest, ProviderExecutionResult,
    ProviderRunHandle, ProviderUsage,
)
from servicefabric_agent_provider_runtime import ProviderRuntime, ProviderRuntimeError


class FakeAdapter:
    provider_id = "fake"

    def __init__(self, argv: tuple[str, ...]) -> None:
        self.argv = argv
        self.received_environment: dict[str, str] | None = None

    def probe(self) -> dict[str, object]:
        return {"available": True}

    def build_argv(self, request: ProviderExecutionRequest) -> tuple[str, ...]:
        return self.argv

    def parse_event(self, raw_event: str, sequence: int) -> ProviderEvent | None:
        if not raw_event:
            return None
        return ProviderEvent(sequence=sequence, event_type="message", timestamp=datetime.now(timezone.utc), payload={"text": raw_event})

    def recover_result(self, handle: ProviderRunHandle, events: tuple[ProviderEvent, ...], usage: ProviderUsage, *, exit_code: int | None) -> ProviderExecutionResult:
        return ProviderExecutionResult(handle=handle, status="success" if exit_code == 0 else "failed", usage=usage)


class ProviderRuntimeTests(unittest.TestCase):
    def request(self, **updates: object) -> ProviderExecutionRequest:
        values: dict[str, object] = {"run_id": "run-1", "task_id": "task-1", "provider_id": "fake", "repository": ".", "prompt": "do work", "timeout_seconds": 2}
        values.update(updates)
        return ProviderExecutionRequest(**values)

    def test_executes_explicit_argv_and_passes_parsed_events_to_adapter(self) -> None:
        adapter = FakeAdapter((sys.executable, "-c", "print('one'); print('two')"))
        result = ProviderRuntime((adapter,)).execute(self.request())
        self.assertEqual(result.status, "success")
        self.assertEqual(result.handle.state, "success")

    def test_unknown_provider_and_invalid_argv_are_rejected(self) -> None:
        runtime = ProviderRuntime()
        with self.assertRaises(ProviderRuntimeError):
            runtime.execute(self.request(provider_id="unknown"))
        with self.assertRaises(ProviderRuntimeError):
            ProviderRuntime((FakeAdapter(()),)).execute(self.request())

    def test_timeout_returns_timeout_and_clears_active_run(self) -> None:
        adapter = FakeAdapter((sys.executable, "-c", "import time; time.sleep(2)"))
        runtime = ProviderRuntime((adapter,))
        result = runtime.execute(self.request(timeout_seconds=1))
        self.assertEqual(result.status, "timeout")
        self.assertEqual(runtime.active_run_ids(), ())

    def test_cancel_terminates_active_run(self) -> None:
        adapter = FakeAdapter((sys.executable, "-c", "import time; time.sleep(5)"))
        runtime = ProviderRuntime((adapter,))
        result: list[ProviderExecutionResult] = []
        thread = Thread(target=lambda: result.append(runtime.execute(self.request())), daemon=True)
        thread.start()
        for _ in range(20):
            if runtime.active_run_ids():
                break
            sleep(0.01)
        self.assertTrue(runtime.cancel("run-1"))
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result[0].status, "failed")
