from __future__ import annotations

import unittest

from servicefabric_agent_provider_contracts import (
    ProviderEvent,
    ProviderExecutionRequest,
    ProviderRunHandle,
    ProviderUsage,
)
from servicefabric_gemini_cli_adapter import GeminiCliAdapter


class GeminiCliAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = GeminiCliAdapter()
        self.request = ProviderExecutionRequest(
            run_id="run-1",
            task_id="task-1",
            provider_id="gemini",
            repository="/workspace",
            prompt="Update the focused package.",
            timeout_seconds=60,
        )
        self.handle = ProviderRunHandle(
            provider_id="gemini",
            run_id="run-1",
            task_id="task-1",
            state="running",
        )

    def test_build_argv_is_non_interactive_and_does_not_launch_a_process(self) -> None:
        self.assertEqual(
            self.adapter.build_argv(self.request),
            (
                "gemini", "--output-format", "stream-json", "--approval-mode", "yolo",
                "--prompt", "Update the focused package.",
            ),
        )

    def test_build_argv_includes_an_explicit_model(self) -> None:
        request = self.request.model_copy(update={"model": "gemini-2.5-pro"})
        self.assertEqual(self.adapter.build_argv(request)[-2:], ("--model", "gemini-2.5-pro"))

    def test_parse_event_accepts_stream_json_and_rejects_unrecognised_input(self) -> None:
        event = self.adapter.parse_event(
            '{"type":"message","timestamp":"2026-07-17T09:00:00Z","content":"working"}', 3
        )
        self.assertEqual(event.sequence, 3)
        self.assertEqual(event.event_type, "message")
        self.assertEqual(event.payload, {"content": "working"})
        self.assertIsNone(self.adapter.parse_event("not-json", 4))
        self.assertIsNone(self.adapter.parse_event('{"type":"other"}', 5))

    def test_recover_result_prefers_terminal_provider_event(self) -> None:
        result = self.adapter.recover_result(
            self.handle,
            (ProviderEvent(
                sequence=0, event_type="result", timestamp=self.adapter._timestamp(None),
                payload={"status": "blocked"},
            ),),
            ProviderUsage(),
            exit_code=0,
        )
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.task_result.status, "blocked")

    def test_recover_result_uses_exit_code_when_no_terminal_event_exists(self) -> None:
        result = self.adapter.recover_result(self.handle, (), ProviderUsage(), exit_code=1)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.task_result.status, "failed")


if __name__ == "__main__":
    unittest.main()
