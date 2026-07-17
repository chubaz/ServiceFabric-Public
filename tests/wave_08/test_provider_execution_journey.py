"""One black-box Wave-8 journey over a recorded Wave-7 durable run."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Lock
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "wave_08"
for source in reversed((
    "packages/servicefabric_contracts/src",
    "packages/servicefabric_agentic_contracts/src",
    "packages/servicefabric_agentic_context/src",
    "packages/servicefabric_agentic_planner/src",
    "packages/servicefabric_agentic_run_store/src",
    "packages/servicefabric_agent_tools/src",
    "packages/servicefabric_agentic_orchestrator/src",
    "packages/servicefabric_agent_harness/src",
    "packages/servicefabric_agent_provider_contracts/src",
    "packages/servicefabric_agent_provider_runtime/src",
    "packages/servicefabric_langgraph_orchestration/src",
    "packages/servicefabric_codex_adapter/src",
    "packages/servicefabric_claude_code_adapter/src",
    "packages/servicefabric_gemini_cli_adapter/src",
    "packages/servicefabric_pi_harness/src",
    "clients/python",
)):
    sys.path.insert(0, str(ROOT / source))

from servicefabric_agent_provider_contracts import ProviderEvent, ProviderUsage
from servicefabric_agentic_contracts import AgentRunPlan
from servicefabric_claude_code_adapter import ClaudeCodeAdapter
from servicefabric_codex_adapter import CodexAdapter
from servicefabric_gemini_cli_adapter import GeminiCliAdapter
from servicefabric_pi_harness import PiHarnessAdapter
from servicefabric_client.agent_providers import ProviderRegistry
from servicefabric_client.agentic import AgenticApplicationService
from servicefabric_client.provider_execution import ProviderExecutionService


class _RecordedExecutableAdapter:
    """Keep real adapter normalization while replacing only its executable."""

    def __init__(self, delegate: object, executable: Path, timeline: Path) -> None:
        self._delegate = delegate
        self._executable = executable
        self._timeline = timeline
        self._attempts: dict[str, int] = {}
        self._lock = Lock()

    @property
    def provider_id(self) -> str:
        return self._delegate.provider_id

    def probe(self) -> dict[str, object]:
        return self._delegate.probe()

    def build_argv(self, request: object) -> tuple[str, ...]:
        # Calling the real renderer guards the same provider/request boundary;
        # only the process image is replaced by the local fixture executable.
        self._delegate.build_argv(request)
        with self._lock:
            attempt = self._attempts.get(request.task_id, 0) + 1
            self._attempts[request.task_id] = attempt
        outcome, delay = self._outcome(request.task_id, attempt)
        return (
            str(self._executable),
            "--provider", self.provider_id,
            "--task", request.task_id,
            "--events", str(FIXTURES / outcome),
            "--timeline", str(self._timeline),
            "--delay", str(delay),
        )

    def parse_event(self, raw_event: str, sequence: int) -> ProviderEvent | None:
        return self._delegate.parse_event(raw_event, sequence)

    def recover_result(self, handle: object, events: tuple[ProviderEvent, ...], usage: ProviderUsage, *, exit_code: int | None):
        totals = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "estimated_cost": 0.0, "duration_ms": 0}
        for event in events:
            if event.event_type != "usage":
                continue
            value = event.payload.get("usage", event.payload)
            if isinstance(value, dict):
                for key in totals:
                    raw = value.get(key, 0)
                    totals[key] += raw if isinstance(raw, (int, float)) else 0
        normalized_usage = ProviderUsage.model_validate(totals)
        result = self._delegate.recover_result(handle, events, normalized_usage, exit_code=exit_code)
        return result.model_copy(update={"usage": normalized_usage})

    def _outcome(self, task_id: str, attempt: int) -> tuple[str, float]:
        if self.provider_id == "codex":
            if attempt == 1:
                return "codex_failure.jsonl", 0.10
            if attempt == 2:
                return "codex_success.jsonl", 5.0
            return "codex_success.jsonl", 0.10
        if self.provider_id == "claude":
            return "claude_success.jsonl", 0.35 if attempt == 1 else 0.70
        if self.provider_id == "pi":
            return "pi_success.jsonl", 0.10
        if self.provider_id == "gemini":
            return "gemini_success.jsonl", 0.10
        raise AssertionError((self.provider_id, task_id, attempt))


class Wave08ProviderExecutionJourneyTests(unittest.TestCase):
    def test_recorded_run_executes_interrupts_resumes_cancels_and_hands_off(self) -> None:
        with tempfile.TemporaryDirectory(prefix="servicefabric-wave8-evaluation-") as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            state_root = root / "state"
            (state_root / "runs").mkdir(parents=True)
            (state_root / "runtime").mkdir(parents=True)
            shutil.copyfile(FIXTURES / "wave7_run.json", state_root / "runs" / "wave8-journey.json")
            runtime = json.loads((FIXTURES / "wave7_runtime.json").read_text(encoding="utf-8"))
            runtime["repository"] = str(repository)
            (state_root / "runtime" / "wave8-journey.json").write_text(
                json.dumps(runtime, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )

            executable = root / "fake-provider"
            shutil.copyfile(FIXTURES / "fake_provider.py", executable)
            executable.chmod(0o755)
            timeline = root / "timeline.jsonl"
            adapters = tuple(
                _RecordedExecutableAdapter(adapter, executable, timeline)
                for adapter in (ClaudeCodeAdapter(), CodexAdapter(), GeminiCliAdapter(), PiHarnessAdapter())
            )
            registry = ProviderRegistry(adapters)
            policy = self._write_json(root / "policy.json", {
                "default_provider": "codex",
                "role_overrides": {"review": "claude", "integration": "gemini"},
                "maximum_parallel_per_provider": 1,
                "timeout_seconds": 10,
            })

            agents = AgenticApplicationService(state_root)
            loaded = agents.status("wave8-journey")
            plan = AgentRunPlan.model_validate(loaded["plan"])
            self.assertEqual(tuple(task.task_id for task in plan.tasks), ("review", "implementation", "integrate"))
            self.assertEqual(loaded["ready_tasks"], ("review", "implementation"))
            self.assertEqual(loaded["handoff"]["task_results"], [])

            execution = ProviderExecutionService(agents, registry)
            first = execution.execute(plan.run_id, policy)
            self.assertEqual(first["interrupt"], "provider_failure")
            initial_timeline = self._timeline(timeline)
            starts = {item["provider"]: item for item in initial_timeline if item["phase"] == "start"}
            stops = {item["provider"]: item for item in initial_timeline if item["phase"] == "finish"}
            self.assertEqual((starts["claude"]["task"], starts["codex"]["task"]), ("review", "implementation"))
            self.assertLess(starts["codex"]["time"], stops["claude"]["time"])
            self.assertLess(starts["claude"]["time"], stops["codex"]["time"])
            self.assertNotEqual(starts["codex"]["pgid"], starts["claude"]["pgid"])

            # A fresh composition resumes the same run from Wave-7 state plus
            # the durable LangGraph-shaped interrupt cursor.
            del execution, agents
            resumed_agents = AgenticApplicationService(state_root)
            execution = ProviderExecutionService(resumed_agents, registry)
            # Re-submit the non-secret policy to the interrupted public entry
            # point because the current interrupt cursor stores only its
            # reason. No task is dispatched while the interrupt is present.
            self.assertEqual(execution.execute(plan.run_id, policy)["interrupt"], "provider_failure")
            retry_both = self._write_json(root / "retry-both.json", {
                "action": "retry", "task_ids": ["review", "implementation"]
            })
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(execution.resume, plan.run_id, retry_both)
                self._wait_for_start(timeline, "codex", occurrence=2)
                cancelled = execution.cancel(plan.run_id, "implementation")
                self.assertEqual(cancelled["cancelled_tasks"], ("implementation",))
                interrupted = pending.result(timeout=5)
            self.assertEqual(interrupted["interrupt"], "provider_failure")
            cancellation_timeline = self._timeline(timeline)
            codex_second = [item for item in cancellation_timeline if item["provider"] == "codex" and item["phase"] == "start"][1]
            claude_second = [item for item in cancellation_timeline if item["provider"] == "claude" and item["phase"] == "finish"][1]
            terminated = [item for item in cancellation_timeline if item["provider"] == "codex" and item["phase"] == "terminated"]
            self.assertEqual(terminated[-1]["pgid"], codex_second["pgid"])
            self.assertEqual(claude_second["status"], 0)

            # Persist a new role decision while interrupted, then resume from a
            # new service instance. Review moves from Claude to Pi.
            pi_policy = self._write_json(root / "pi-policy.json", {
                "default_provider": "codex",
                "role_overrides": {"review": "pi", "integration": "gemini"},
                "maximum_parallel_per_provider": 1,
                "timeout_seconds": 10,
            })
            self.assertEqual(execution.execute(plan.run_id, pi_policy)["interrupt"], "provider_failure")
            del execution, resumed_agents
            resumed_agents = AgenticApplicationService(state_root)
            execution = ProviderExecutionService(resumed_agents, registry)
            retry_selected = self._write_json(root / "retry-selected.json", {
                "action": "retry", "task_ids": ["review", "implementation"]
            })
            resumed = execution.resume(plan.run_id, retry_selected)
            self.assertEqual(resumed["run_id"], plan.run_id)
            self.assertEqual(tuple(task.task_id for task in resumed_agents.ready(plan.run_id)), ("integrate",))

            # Simulate orchestration-process interruption once more. The
            # dependent task is discovered solely from durable Wave-7 results.
            del execution, resumed_agents
            final_agents = AgenticApplicationService(state_root)
            self.assertEqual(tuple(task.task_id for task in final_agents.ready(plan.run_id)), ("integrate",))
            final_execution = ProviderExecutionService(final_agents, registry)
            completed = final_execution.execute(plan.run_id, pi_policy)
            expected_handoff = json.loads((FIXTURES / "expected_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(completed["handoff"], expected_handoff)
            self.assertEqual(final_agents.handoff(plan.run_id).model_dump(mode="json"), expected_handoff)

            events = final_execution.events(plan.run_id)
            expected_event_count = 0
            for fixture in FIXTURES.glob("*_*.jsonl"):
                expected_event_count += len(fixture.read_text(encoding="utf-8").splitlines())
            # Claude runs twice and Codex success runs twice; the cancelled
            # Codex executable emits no fixture before termination.
            expected_event_count += len((FIXTURES / "claude_success.jsonl").read_text(encoding="utf-8").splitlines())
            self.assertEqual(len(events), expected_event_count)
            for value in events:
                ProviderEvent.model_validate({key: item for key, item in value.items() if key != "task_id"})
            self.assertTrue(any(item["payload"].get("api_token") == "[redacted]" for item in events))

            usage_lines = (state_root / "provider-usage" / f"{plan.run_id}.jsonl").read_text(encoding="utf-8").splitlines()
            usages = [json.loads(line)["usage"] for line in usage_lines]
            self.assertEqual(sum(item["input_tokens"] for item in usages), 190)
            self.assertAlmostEqual(sum(item["estimated_cost"] for item in usages), 0.95)

            persisted_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted(state_root.rglob("*"))
                if path.is_file()
            )
            self.assertNotIn("fixture-secret", persisted_text)
            for forbidden_key in ('"argv"', '"command"', '"environment"', '"shell"'):
                self.assertNotIn(forbidden_key, persisted_text)
            self.assertNotIn("PATH", persisted_text)

    @staticmethod
    def _write_json(path: Path, value: object) -> Path:
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _timeline(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def _wait_for_start(self, path: Path, provider: str, *, occurrence: int) -> None:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if path.exists():
                count = sum(item["provider"] == provider and item["phase"] == "start" for item in self._timeline(path))
                if count >= occurrence:
                    return
            time.sleep(0.01)
        self.fail(f"fake {provider} executable did not start")

if __name__ == "__main__":
    unittest.main()
