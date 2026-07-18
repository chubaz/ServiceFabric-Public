"""Focused black-box composition tests for the Wave-9 factory."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from servicefabric_agent_provider_contracts import ProviderEvent, ProviderUsage
from servicefabric_agentic_contracts import (
    AgentTaskResult,
    ApplicationIntent,
    VerificationEvidence,
)
from servicefabric_application_factory_contracts import (
    FactoryApprovalDecision,
    UnmetRequirement,
)
from servicefabric_blueprints import (
    ApplicationBlueprint,
    BlueprintCatalog,
    BlueprintModule,
)
from servicefabric_client.agent_providers import ProviderRegistry
from servicefabric_client.agentic import AgenticApplicationService
from servicefabric_client.application_factory import (
    ApplicationFactoryService,
    FactoryStateError,
)
from servicefabric_client.provider_execution import ProviderExecutionService
from servicefabric_codex_adapter import CodexAdapter


ROOT = Path(__file__).resolve().parents[2]
WAVE_08_FIXTURES = ROOT / "tests" / "fixtures" / "wave_08"
MODULES = ("api", "data", "jobs", "security", "web")
EXPECTED_LANES = tuple(f"module-{module_id}" for module_id in MODULES) + (
    "application-integration",
    "application-assurance",
)


class _ExecutionSpy:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Path]] = []

    def execute(self, run_id: str, policy_path: str | Path) -> dict[str, object]:
        path = Path(policy_path)
        self.calls.append((run_id, path))
        return {"run_id": run_id, "handoff": {"status": "pending"}}

    def events(self, run_id: str, task_id: str | None = None) -> tuple[dict[str, object], ...]:
        return ()

    def usage(self, run_id: str) -> tuple[dict[str, object], ...]:
        return ()


class _RecordedCodexAdapter:
    """Retain Codex normalization while replacing only the process image."""

    def __init__(self, executable: Path, timeline: Path) -> None:
        self._delegate = CodexAdapter()
        self._executable = executable
        self._timeline = timeline

    @property
    def provider_id(self) -> str:
        return self._delegate.provider_id

    def probe(self) -> dict[str, object]:
        return self._delegate.probe()

    def build_argv(self, request: object) -> tuple[str, ...]:
        self._delegate.build_argv(request)
        return (
            str(self._executable),
            "--provider",
            self.provider_id,
            "--task",
            request.task_id,
            "--events",
            str(WAVE_08_FIXTURES / "codex_success.jsonl"),
            "--timeline",
            str(self._timeline),
            "--delay",
            "0.01",
        )

    def parse_event(self, raw_event: str, sequence: int) -> ProviderEvent | None:
        return self._delegate.parse_event(raw_event, sequence)

    def recover_result(
        self,
        handle: object,
        events: tuple[ProviderEvent, ...],
        usage: ProviderUsage,
        *,
        exit_code: int | None,
    ):
        totals: dict[str, int | float] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "estimated_cost": 0.0,
            "duration_ms": 0,
        }
        for event in events:
            if event.event_type != "usage":
                continue
            value = event.payload.get("usage", event.payload)
            if not isinstance(value, dict):
                continue
            for key in totals:
                item = value.get(key, 0)
                if isinstance(item, (int, float)):
                    totals[key] += item
        normalized = ProviderUsage.model_validate(totals)
        result = self._delegate.recover_result(
            handle,
            events,
            normalized,
            exit_code=exit_code,
        )
        return result.model_copy(update={"usage": normalized})


class ApplicationFactoryCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="servicefabric-wave9-")
        self.root = Path(self.temporary.name)
        self.repository = self.root / "sample-app"
        self.state = self.root / "state"
        self.policy = self.root / "provider-policy.json"
        self.policy.write_text(
            json.dumps(
                {
                    "default_provider": "codex",
                    "role_overrides": {
                        "assurance": "codex",
                        "integration": "codex",
                    },
                    "maximum_parallel_per_provider": 5,
                    "timeout_seconds": 10,
                }
            ),
            encoding="utf-8",
        )
        self.intent = ApplicationIntent(
            intent_id="sample-factory",
            mode="create",
            application_id="sample-app",
            objective="Create a reviewed sample application",
        )
        self.catalog = BlueprintCatalog()
        self.catalog.register(self._blueprint("sample-blueprint"))
        self.agents = AgenticApplicationService(self.state / "agent-runs")
        self.timeline = self.root / "provider-timeline.jsonl"
        executable = self.root / "fake-provider"
        shutil.copyfile(WAVE_08_FIXTURES / "fake_provider.py", executable)
        executable.chmod(0o755)
        self.execution = ProviderExecutionService(
            self.agents,
            ProviderRegistry((_RecordedCodexAdapter(executable, self.timeline),)),
        )
        self.service = ApplicationFactoryService(
            self.state,
            blueprint_catalog=self.catalog,
            agent_service=self.agents,
            provider_execution=self.execution,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_plan_composes_seven_lanes_and_blocks_unresolved_resources(self) -> None:
        planned = self._plan()

        self.assertEqual("pending_approval", planned["status"])
        self.assertTrue(planned["technology_profile"].approved)
        engineering = planned["engineering_blueprint"]
        self.assertEqual(EXPECTED_LANES, tuple(lane.lane_id for lane in engineering.lanes))
        self.assertEqual(7, len(engineering.lanes))
        self.assertEqual(
            {
                f"module-{module_id}": (module_id,)
                for module_id in MODULES
            }
            | {
                "application-integration": (),
                "application-assurance": (),
            },
            {lane.lane_id: lane.module_ids for lane in engineering.lanes},
        )
        self.assertEqual(
            {f"module-{module_id}": (f"components/{module_id}",) for module_id in MODULES}
            | {
                "application-integration": (".servicefabric/application-integration",),
                "application-assurance": (".servicefabric/application-assurance",),
            },
            {lane.lane_id: lane.allowed_paths for lane in engineering.lanes},
        )
        self.assertEqual(
            {module_id: (f"technique-{module_id}-v1",) for module_id in MODULES},
            {
                selection.module_id: selection.technique_policy_ids
                for selection in planned["technology_profile"].module_selections
            },
        )
        self.assertEqual(engineering.agent_run_plan, planned["plan"])
        self.assertEqual(
            planned["plan"].model_dump(mode="json"),
            self.agents.store.load(planned["run_id"])["plan"],
        )
        self.assertFalse(self.repository.exists())

        blocked_repository = self.root / "blocked-app"
        blocked_catalog = BlueprintCatalog()
        blocked_catalog.register(self._blueprint("blocked-blueprint", unresolved_resource=True))
        blocked_agents = AgenticApplicationService(self.root / "blocked-state" / "agent-runs")
        blocked_execution = _ExecutionSpy()
        blocked_service = ApplicationFactoryService(
            self.root / "blocked-state",
            blueprint_catalog=blocked_catalog,
            agent_service=blocked_agents,
            provider_execution=blocked_execution,
            resource_resolver=lambda _request: False,
        )
        blocked = blocked_service.plan(
            intent=ApplicationIntent(
                intent_id="blocked-factory",
                mode="create",
                application_id="blocked-app",
                objective="Require an unresolved reviewed resource",
            ),
            blueprint_id="blocked-blueprint",
            repository=blocked_repository,
            provider_policy=self.policy,
            technique_policy_ids=self._technique_policy_ids(),
        )

        self.assertEqual("blocked", blocked["status"])
        self.assertTrue(blocked["unmet_requirements"])
        self.assertTrue(
            all(isinstance(item, UnmetRequirement) for item in blocked["unmet_requirements"])
        )
        self.assertFalse(blocked_repository.exists())
        self.assertFalse((self.root / "blocked-state" / "worktrees").exists())
        with self.assertRaises(FactoryStateError):
            blocked_service.bootstrap(blocked["run_id"])
        with self.assertRaises(FactoryStateError):
            blocked_service.execute(blocked["run_id"])
        self.assertEqual([], blocked_execution.calls)

    def test_bootstrap_creates_exact_base_for_all_seven_engineering_lanes(self) -> None:
        planned = self._approved_plan()
        bootstrapped = self.service.bootstrap(planned["run_id"])

        base = bootstrapped["base_commit"]
        self.assertEqual(base, self._git(self.repository, "rev-parse", "HEAD"))
        self.assertEqual(
            base,
            self._git(Path(bootstrapped["integration_worktree"]), "rev-parse", "HEAD"),
        )
        self.assertEqual(
            f"factory/{planned['run_id']}/integration",
            bootstrapped["integration_branch"],
        )
        self.assertEqual(
            set(EXPECTED_LANES) - {"application-integration"},
            set(bootstrapped["lanes"]),
        )
        for lane_id, lane in bootstrapped["lanes"].items():
            self.assertEqual(
                f"factory/{planned['run_id']}/lane/{lane_id}", lane["branch"]
            )
            self.assertEqual(base, self._git(Path(lane["worktree"]), "rev-parse", "HEAD"))

        for lane_id in EXPECTED_LANES:
            guidance = self.repository / ".servicefabric" / "factory" / "lanes" / f"{lane_id}.md"
            self.assertTrue(guidance.is_file(), lane_id)
            self.assertIn(f"Engineering Lane: {lane_id}", guidance.read_text(encoding="utf-8"))
        for module_id in MODULES:
            agents = self.repository / "components" / module_id / "AGENTS.md"
            value = agents.read_text(encoding="utf-8")
            self.assertIn(f"Engineering Lane: module-{module_id}", value)
            self.assertIn(f"technique-{module_id}-v1", value)

    def test_fake_executable_provider_journey_retries_and_integrates_latest_shas(self) -> None:
        planned = self._approved_plan()
        bootstrap = self.service.bootstrap(planned["run_id"])
        run_id = planned["run_id"]

        for expected_status in ("running", "running", "success"):
            execution = self.service.execute(run_id)
            self.assertEqual(expected_status, execution["handoff"]["status"])

        provider_results = self.agents.store.load(run_id)["results"]
        self.assertEqual(set(EXPECTED_LANES), set(provider_results))
        self.assertTrue(
            all(
                AgentTaskResult.model_validate(value).status == "success"
                for value in provider_results.values()
            )
        )

        timeline = self._json_lines(self.timeline)
        self.assertEqual(7, sum(item["phase"] == "start" for item in timeline))
        self.assertEqual(7, sum(item["phase"] == "finish" for item in timeline))
        self.assertEqual({"codex"}, {item["provider"] for item in timeline})
        self.assertEqual(set(EXPECTED_LANES), {item["task"] for item in timeline})

        initial_lane = Path(bootstrap["lanes"]["module-api"]["worktree"])
        initial_sha = self._commit_candidate(
            initial_lane,
            "components/api/initial.txt",
            "returned candidate\n",
            "feat: initial api candidate",
        )
        self.agents.record_result(
            run_id,
            "module-api",
            self._result(
                "module-api",
                initial_sha,
                ("components/api/initial.txt",),
                status="failed",
            ),
        )
        with self.assertRaises(FactoryStateError):
            self.service.review(
                run_id,
                "module-api",
                {
                    "decision_id": "mutable-api-review",
                    "commit_sha": bootstrap["lanes"]["module-api"]["branch"],
                    "decision": "rework",
                    "decided_by": "factory-reviewer",
                },
            )
        returned = self.service.review(
            run_id,
            "module-api",
            {
                "decision_id": "return-initial-api",
                "decision": "rework",
                "reason": "Initial candidate requires revision.",
                "decided_by": "factory-reviewer",
            },
        )
        self.assertEqual("rework", returned.decision)
        self.assertEqual(initial_sha, returned.commit_sha)

        replacement_worktree = self.root / "replacement-api"
        self._git(
            self.repository,
            "worktree",
            "add",
            "--detach",
            str(replacement_worktree),
            bootstrap["base_commit"],
        )
        replacement_sha = self._commit_candidate(
            replacement_worktree,
            "components/api/result.txt",
            "revised api candidate\n",
            "feat: revised api candidate",
        )
        candidate_shas = {"module-api": replacement_sha}
        self.agents.record_result(
            run_id,
            "module-api",
            self._result("module-api", replacement_sha, ("components/api/result.txt",)),
        )
        current = {
            item["task_id"]: item for item in self.service.candidates(run_id)["candidates"]
        }
        self.assertEqual("pending", current["module-api"]["review_state"])

        for module_id in MODULES[1:]:
            task_id = f"module-{module_id}"
            lane = Path(bootstrap["lanes"][task_id]["worktree"])
            changed_path = f"components/{module_id}/result.txt"
            candidate_sha = self._commit_candidate(
                lane,
                changed_path,
                f"accepted {module_id} candidate\n",
                f"feat: {module_id} candidate",
            )
            candidate_shas[task_id] = candidate_sha
            self.agents.record_result(
                run_id,
                task_id,
                self._result(task_id, candidate_sha, (changed_path,)),
            )

        for task_id in tuple(f"module-{module_id}" for module_id in MODULES):
            reviewed = self.service.review(
                run_id,
                task_id,
                {
                    "decision_id": f"accept-{task_id}",
                    "decision": "accept",
                    "reason": "Exact candidate and evidence accepted.",
                    "decided_by": "factory-reviewer",
                },
            )
            self.assertEqual(candidate_shas[task_id], reviewed.commit_sha)
            self.assertEqual(40, len(reviewed.commit_sha))

        candidates = {
            item["task_id"]: item for item in self.service.candidates(run_id)["candidates"]
        }
        self.assertEqual(set(EXPECTED_LANES), set(candidates))
        for task_id, commit_sha in candidate_shas.items():
            self.assertEqual(commit_sha, candidates[task_id]["commit_sha"])
            self.assertEqual("accept", candidates[task_id]["review_state"])
            self.assertTrue(candidates[task_id]["changed_paths"])
            self.assertTrue(candidates[task_id]["evidence"])

        handoff = self.service.integrate(run_id)

        self.assertEqual("success", handoff.status)
        self.assertIsNotNone(handoff.integration_commit)
        self.assertIn(f"provider-usage:{run_id}", handoff.verification_evidence)
        self.assertEqual(
            tuple(f"accept-module-{module_id}" for module_id in MODULES),
            handoff.review_decision_refs,
        )
        integration = Path(bootstrap["integration_worktree"])
        self.assertFalse((integration / "components/api/initial.txt").exists())
        self.assertEqual(
            "revised api candidate\n",
            (integration / "components/api/result.txt").read_text(encoding="utf-8"),
        )
        self.assertEqual(bootstrap["base_commit"], self._git(self.repository, "rev-parse", "HEAD"))

        status = self.service.status(run_id)
        self.assertEqual("success", status["factory_state"])
        self.assertEqual(handoff.integration_commit, status["integration_commit"])
        self.assertEqual((initial_sha,), status["superseded_candidate_shas"])
        self.assertEqual(7, len(status["usage"]))
        self.assertEqual(28, len(status["events"]))
        self.assertEqual(140, sum(item["usage"]["input_tokens"] for item in status["usage"]))
        for value in status["events"]:
            ProviderEvent.model_validate(
                {key: item for key, item in value.items() if key != "task_id"}
            )
        self.assertEqual(handoff, self.service.handoff(run_id))
        self.assertNotIn("input_tokens", handoff.model_dump_json())
        self.assertEqual(
            self.service.handoff(run_id).model_dump_json(),
            self.service.handoff(run_id).model_dump_json(),
        )

    def _plan(self) -> dict[str, object]:
        return self.service.plan(
            intent=self.intent,
            blueprint_id="sample-blueprint",
            repository=self.repository,
            provider_policy=self.policy,
            technique_policy_ids=self._technique_policy_ids(),
        )

    def _approved_plan(self) -> dict[str, object]:
        planned = self._plan()
        self.service.approve(
            planned["run_id"],
            FactoryApprovalDecision(
                decision_id="approve-sample-factory",
                run_id=planned["run_id"],
                subject_ref=planned["approval_subject_ref"],
                decision="approve",
                reason="Reviewed profile and blueprint approved.",
                decided_by="factory-approver",
            ),
        )
        return planned

    @staticmethod
    def _technique_policy_ids() -> dict[str, tuple[str, ...]]:
        return {module_id: (f"technique-{module_id}-v1",) for module_id in MODULES}

    @classmethod
    def _blueprint(
        cls,
        blueprint_id: str,
        *,
        unresolved_resource: bool = False,
    ) -> ApplicationBlueprint:
        return ApplicationBlueprint(
            blueprint_id=blueprint_id,
            version="1.0.0",
            title="Seven Lane Application",
            description="Five reviewed modules compiled with integration and assurance.",
            modules=tuple(
                cls._module(module_id, unresolved_resource=unresolved_resource and index == 0)
                for index, module_id in enumerate(MODULES)
            ),
        )

    @staticmethod
    def _module(module_id: str, *, unresolved_resource: bool) -> BlueprintModule:
        requires = (
            {
                "resources": [
                    {
                        "id": "external-database",
                        "type": "relational-database",
                        "scope": "application",
                    }
                ]
            }
            if unresolved_resource
            else None
        )
        specification: dict[str, object] = {
            "primitive": "service",
            "kit": "fastapi-service @ServiceFabric/reviewed/fastapi-service-1.0.0.json",
            "source": f"components/{module_id}",
            "provides": [
                {"id": f"{module_id}-api", "type": "http", "protocol": "http"}
            ],
            "lifecycle": {
                "readiness": {"type": "http", "path": "/health"},
                "shutdown": {"timeoutSeconds": 10},
            },
        }
        if requires is not None:
            specification["requires"] = requires
        return BlueprintModule.from_manifest(
            {
                "apiVersion": "servicefabric.local/v1",
                "kind": "ApplicationModule",
                "metadata": {"id": module_id, "version": "1.0.0"},
                "spec": specification,
            }
        )

    @staticmethod
    def _result(
        task_id: str,
        commit_sha: str,
        changed_paths: tuple[str, ...],
        *,
        status: str = "success",
    ) -> AgentTaskResult:
        return AgentTaskResult(
            task_id=task_id,
            status=status,
            commit_sha=commit_sha,
            changed_paths=changed_paths,
            evidence=(
                VerificationEvidence(
                    command="python3 -m unittest",
                    exit_code=0,
                    summary="candidate verification passed",
                ),
            ),
        )

    def _commit_candidate(
        self,
        repository: Path,
        relative_path: str,
        content: str,
        message: str,
    ) -> str:
        candidate_path = repository / relative_path
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(content, encoding="utf-8")
        self._git(repository, "add", relative_path)
        self._git(
            repository,
            "-c",
            "user.name=Factory Test",
            "-c",
            "user.email=factory-test@example.invalid",
            "commit",
            "-m",
            message,
        )
        return self._git(repository, "rev-parse", "HEAD")

    @staticmethod
    def _json_lines(path: Path) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]

    @staticmethod
    def _git(repository: Path, *arguments: str) -> str:
        completed = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()


if __name__ == "__main__":
    unittest.main()
