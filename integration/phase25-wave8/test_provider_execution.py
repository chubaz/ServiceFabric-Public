"""Black-box composition checks using a fake executable, never a provider."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
for source in reversed((
    ROOT / "packages" / "servicefabric_contracts" / "src",
    ROOT / "packages" / "servicefabric_agentic_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_harness" / "src",
    ROOT / "packages" / "servicefabric_agentic_orchestrator" / "src",
    ROOT / "packages" / "servicefabric_agentic_run_store" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_contracts" / "src",
    ROOT / "packages" / "servicefabric_agent_provider_runtime" / "src",
    ROOT / "packages" / "servicefabric_langgraph_orchestration" / "src",
    ROOT / "clients" / "python",
)):
    sys.path.insert(0, str(source))

from servicefabric_agent_provider_contracts import ProviderEvent, ProviderExecutionResult, ProviderRunHandle, ProviderUsage
from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, AgentTaskResult, ApplicationIntent
from servicefabric_agentic_run_store import FileRunStore
from servicefabric_client.agent_providers import ProviderRegistry
from servicefabric_client.provider_execution import ProviderExecutionService


class _FakeAgents:
    def __init__(self, root: Path, plan: AgentRunPlan) -> None:
        self.state_root = root
        self.store = FileRunStore(root / "runs")
        self.store.save_plan(plan)
        self.plan = plan

    def _load(self, run_id: str): return self.plan, self.store.load(run_id)
    def _load_runtime(self, run_id: str): return {"repository": str(self.state_root)}
    def record_result(self, run_id: str, task_id: str, result: AgentTaskResult): self.store.record_result(run_id, result); return result
    def handoff(self, run_id: str): return self.store.handoff(run_id)


class _FakeAdapter:
    provider_id = "fake"
    def probe(self): return {"provider_id": "fake"}
    def build_argv(self, request): return (sys.executable, "-c", "print('{\\\"type\\\":\\\"message\\\",\\\"api_token\\\":\\\"redact\\\"}')")
    def parse_event(self, raw, sequence): return ProviderEvent(sequence=sequence, event_type="message", timestamp=datetime.now(timezone.utc), payload=json.loads(raw))
    def recover_result(self, handle, events, usage, *, exit_code): return ProviderExecutionResult(handle=handle, status="success", usage=usage)


class ProviderExecutionCompositionTests(unittest.TestCase):
    def test_executes_ready_task_persists_result_and_redacts_event_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = AgentRunPlan(run_id="run-1", intent=ApplicationIntent(intent_id="intent-1", mode="modify", objective="test"), maximum_parallel_tasks=1, tasks=(AgentTask(task_id="task-1", role="implementation", objective="test"),))
            policy = root / "policy.json"
            policy.write_text(json.dumps({"default_provider": "fake", "maximum_parallel_per_provider": 1, "timeout_seconds": 10}), encoding="utf-8")
            service = ProviderExecutionService(_FakeAgents(root, plan), ProviderRegistry((_FakeAdapter(),)))
            result = service.execute("run-1", policy)
            self.assertEqual(result["handoff"]["status"], "success")
            event = service.events("run-1")[0]
            self.assertEqual(event["payload"]["api_token"], "[redacted]")

