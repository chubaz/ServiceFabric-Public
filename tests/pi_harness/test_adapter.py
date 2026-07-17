from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
for source in reversed((
    ROOT / "packages" / "servicefabric_contracts" / "src",
    ROOT / "packages" / "servicefabric_agentic_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_contracts" / "src",
    ROOT / "packages" / "servicefabric_pi_harness" / "src",
)):
    sys.path.insert(0, str(source))

from servicefabric_agent_provider_contracts import (
    ProviderExecutionRequest,
    ProviderRunHandle,
    ProviderUsage,
)
from servicefabric_pi_harness import PiHarnessAdapter


class PiHarnessAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = PiHarnessAdapter()
        self.request = ProviderExecutionRequest(
            run_id="run-1", task_id="task-1", provider_id="pi",
            repository="/workspace", prompt="implement this", timeout_seconds=60,
        )

    def test_build_argv_is_data_only_and_accepts_model_options(self) -> None:
        request = self.request.model_copy(update={"model": "pi-model", "maximum_turns": 3})
        self.assertEqual(
            self.adapter.build_argv(request),
            ("pi", "--print", "--output-format", "json", "--model", "pi-model", "--max-turns", "3", "implement this"),
        )
        with self.assertRaises(ValueError):
            self.adapter.build_argv(self.request.model_copy(update={"provider_id": "other"}))

    def test_parse_event_maps_json_records_and_contains_malformed_output(self) -> None:
        event = self.adapter.parse_event(
            '{"type":"tool_call","timestamp":"2026-07-17T10:00:00Z","name":"read_file"}', 4,
        )
        assert event is not None
        self.assertEqual(event.event_type, "tool_use")
        self.assertEqual(event.sequence, 4)
        self.assertEqual(event.timestamp, datetime(2026, 7, 17, 10, tzinfo=timezone.utc))
        self.assertEqual(self.adapter.parse_event('{"type":"unrecognised"}', 5), None)
        warning = self.adapter.parse_event("not json", 6)
        assert warning is not None
        self.assertEqual(warning.event_type, "warning")

    def test_recover_result_never_manages_a_process(self) -> None:
        handle = ProviderRunHandle(provider_id="pi", run_id="run-1", task_id="task-1", state="running")
        result = self.adapter.recover_result(handle, (), ProviderUsage(), exit_code=0)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.handle.state, "success")
        failed = self.adapter.recover_result(handle, (), ProviderUsage(), exit_code=1)
        self.assertEqual(failed.status, "failed")
        unknown = self.adapter.recover_result(handle, (), ProviderUsage(), exit_code=None)
        self.assertEqual(unknown.status, "unknown")
