from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
for source in reversed((
    ROOT / "packages" / "servicefabric_contracts" / "src",
    ROOT / "packages" / "servicefabric_agentic_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_contracts" / "src",
    ROOT / "packages" / "servicefabric_claude_code_adapter" / "src",
)):
    sys.path.insert(0, str(source))

from servicefabric_agent_provider_contracts import (
    ProviderExecutionRequest,
    ProviderRunHandle,
    ProviderUsage,
)
from servicefabric_claude_code_adapter import ClaudeCodeAdapter


class ClaudeCodeAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = ClaudeCodeAdapter()
        self.request = ProviderExecutionRequest(
            run_id="run-1",
            task_id="task-1",
            provider_id="claude",
            repository="/workspace",
            prompt="Implement only the assigned task.",
            timeout_seconds=60,
            maximum_turns=3,
            model="claude-sonnet",
        )

    def test_builds_a_bounded_noninteractive_json_command(self) -> None:
        self.assertEqual(
            self.adapter.build_argv(self.request),
            (
                "claude", "--print", "--output-format", "stream-json", "--verbose",
                "--model", "claude-sonnet", "--max-turns", "3",
                "Implement only the assigned task.",
            ),
        )
        self.assertEqual(self.adapter.probe()["execution_owned_by"], "provider-runtime")

    def test_rejects_a_request_for_another_provider(self) -> None:
        with self.assertRaisesRegex(ValueError, "provider_id"):
            self.adapter.build_argv(self.request.model_copy(update={"provider_id": "codex"}))

    def test_parses_known_json_events_and_ignores_malformed_input(self) -> None:
        event = self.adapter.parse_event(
            '{"type":"assistant","timestamp":"2026-07-17T10:00:00Z","message":"working"}', 2,
        )
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.event_type, "message")
        self.assertEqual(event.sequence, 2)
        self.assertIsNone(self.adapter.parse_event("not json", 3))
        self.assertIsNone(self.adapter.parse_event('{"type":"unexpected"}', 4))

    def test_recovers_success_failure_and_unknown_without_task_effects(self) -> None:
        handle = ProviderRunHandle(provider_id="claude", run_id="run-1", task_id="task-1", state="running")
        success_event = self.adapter.parse_event('{"type":"result","is_error":false}', 0)
        failure_event = self.adapter.parse_event('{"type":"result","is_error":true}', 1)
        assert success_event is not None and failure_event is not None

        success = self.adapter.recover_result(handle, (success_event,), ProviderUsage(), exit_code=0)
        failure = self.adapter.recover_result(handle, (failure_event,), ProviderUsage(), exit_code=0)
        unknown = self.adapter.recover_result(handle, (), ProviderUsage(), exit_code=None)

        self.assertEqual(success.status, "success")
        self.assertIsNone(success.task_result)
        self.assertEqual(failure.status, "failed")
        self.assertEqual(unknown.status, "unknown")
