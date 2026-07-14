"""Adversarial regressions for the AP-00C managed process runtime."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_application_model",
    "servicefabric_framework_kits",
    "servicefabric_process_runtime",
    "servicefabric_workspace",
):
    sys.path.insert(0, str(ROOT / "packages" / package))

from servicefabric_process_runtime.controller import ManagedProcessController
from servicefabric_process_runtime.identity import (
    get_process_fields,
    is_owned_process,
)
from servicefabric_process_runtime.ports import allocate_loopback_port
from servicefabric_process_runtime.records import (
    ModuleRuntimeRecord,
    ModuleRuntimeStore,
)
from servicefabric_workspace import WorkspaceLayout


class ProcessRuntimeAdversarialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = WorkspaceLayout.from_root(Path(self.temporary.name))
        self.store = ModuleRuntimeStore(self.workspace)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_stale_pid_record_is_marked_failed_without_signaling_owner(self) -> None:
        fields = get_process_fields(os.getpid())
        self.assertIsNotNone(fields)
        stale_start_ticks = fields[1] - 1 if fields else -1
        self.store.save(
            ModuleRuntimeRecord(
                application_id="app",
                module_id="api",
                adapter_id="fastapi-service",
                state="running",
                pid=os.getpid(),
                process_start_ticks=stale_start_ticks,
                port=43210,
                health="healthy",
            )
        )

        status = ManagedProcessController(self.workspace).status("app", "api")

        os.kill(os.getpid(), 0)
        self.assertEqual(status.state, "failed")
        self.assertIsNone(status.identity)
        self.assertIsNone(status.port)
        reloaded = self.store.load("app", "api")
        self.assertIsNotNone(reloaded)
        self.assertIsNone(reloaded.pid if reloaded else None)

    def test_stale_pid_resources_return_no_live_measurements_or_peak_growth(self) -> None:
        self.store.save(
            ModuleRuntimeRecord(
                application_id="app",
                module_id="api",
                adapter_id="fastapi-service",
                state="running",
                pid=os.getpid(),
                process_start_ticks=-1,
                peak_memory_bytes=12345,
            )
        )

        snapshot = ManagedProcessController(self.workspace).resources("app", "api")

        self.assertIsNone(snapshot.current_memory_bytes)
        self.assertEqual(snapshot.peak_memory_bytes, 12345)
        self.assertIsNone(snapshot.recent_cpu_percent)

    def test_malformed_runtime_record_is_ignored_not_partially_trusted(self) -> None:
        record_path = self.store.get_record_path("app", "api")
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text('{"state": "running", "pid": %d}' % os.getpid(), encoding="utf-8")

        self.assertIsNone(self.store.load("app", "api"))
        status = ManagedProcessController(self.workspace).status("app", "api")
        self.assertEqual(status.state, "stopped")
        self.assertIsNone(status.identity)

    def test_pending_atomic_write_fragment_is_not_loaded_as_runtime_state(self) -> None:
        good = ModuleRuntimeRecord(
            application_id="app",
            module_id="api",
            adapter_id="fastapi-service",
            state="stopped",
            peak_memory_bytes=9000,
        )
        self.store.save(good)
        pending = self.store.get_record_path("app", "api").with_name(".sf-atomic-interrupted")
        pending.write_text(
            json.dumps(
                {
                    "application_id": "app",
                    "module_id": "api",
                    "adapter_id": "fastapi-service",
                    "state": "running",
                    "pid": os.getpid(),
                }
            ),
            encoding="utf-8",
        )

        reloaded = self.store.load("app", "api")

        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.state if reloaded else None, "stopped")
        self.assertEqual(reloaded.peak_memory_bytes if reloaded else None, 9000)

    def test_process_ownership_requires_exact_command_prefix(self) -> None:
        fields = get_process_fields(os.getpid())
        self.assertIsNotNone(fields)
        start_ticks = fields[1] if fields else -1

        self.assertFalse(
            is_owned_process(
                os.getpid(),
                start_ticks,
                Path(sys.executable),
                ["-c", "print('forged command')"],
            )
        )

    def test_loopback_port_allocator_never_binds_wildcard_interface(self) -> None:
        observed_addresses: list[tuple[str, int]] = []

        class FakeSocket:
            def bind(self, address: tuple[str, int]) -> None:
                observed_addresses.append(address)

            def getsockname(self) -> tuple[str, int]:
                return ("127.0.0.1", 39123)

            def close(self) -> None:
                pass

        with patch("socket.socket", return_value=FakeSocket()):
            port = allocate_loopback_port()

        self.assertEqual(port, 39123)
        self.assertEqual(observed_addresses, [("127.0.0.1", 0)])


if __name__ == "__main__":
    unittest.main()
