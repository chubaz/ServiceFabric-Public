from datetime import datetime, timezone
import unittest

from pydantic import ValidationError
from servicefabric_agent_provider_contracts import (
    ProviderEvent, ProviderExecutionRequest, ProviderPolicy, ProviderUsage,
)


class ProviderContractTests(unittest.TestCase):
    def test_execution_request_is_immutable_and_rejects_credentials(self) -> None:
        request = ProviderExecutionRequest(
            run_id="run-1", task_id="task-1", provider_id="codex",
            repository="/repo", prompt="implement", timeout_seconds=60,
            environment_names=("CI",), metadata={"source": "test"},
        )
        with self.assertRaises(ValidationError):
            request.timeout_seconds = 30
        with self.assertRaises(ValidationError):
            ProviderExecutionRequest(
                run_id="run-1", task_id="task-1", provider_id="codex",
                repository="/repo", prompt="implement", timeout_seconds=60,
                metadata={"api_token": "not-allowed"},
            )

    def test_event_usage_and_policy_are_strict_and_deterministic(self) -> None:
        event = ProviderEvent(sequence=0, event_type="init", timestamp=datetime.now(timezone.utc))
        self.assertEqual(event.sequence, 0)
        self.assertEqual(ProviderUsage().duration_ms, 0)
        policy = ProviderPolicy(default_provider="codex", role_overrides={"review": "claude"}, maximum_parallel_per_provider=1, timeout_seconds=60)
        self.assertEqual(policy.provider_for_role("review"), "claude")
        self.assertEqual(policy.provider_for_role("implementation"), "codex")
