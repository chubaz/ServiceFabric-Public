"""Focused black-box composition tests for the Wave-9 factory."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from servicefabric_agentic_contracts import (
    AgentTaskResult,
    ApplicationIntent,
    VerificationEvidence,
)
from servicefabric_application_factory_contracts import FactoryApprovalDecision
from servicefabric_blueprints import (
    ApplicationBlueprint,
    BlueprintCatalog,
    BlueprintModule,
)
from servicefabric_client.agentic import AgenticApplicationService
from servicefabric_client.application_factory import ApplicationFactoryService


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
                    "maximum_parallel_per_provider": 2,
                    "timeout_seconds": 60,
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
        self.catalog.register(
            ApplicationBlueprint(
                blueprint_id="sample-blueprint",
                version="1.0.0",
                title="Sample Application",
                description="One reviewed service module.",
                modules=(
                    BlueprintModule.from_manifest(
                        {
                            "apiVersion": "servicefabric.local/v1",
                            "kind": "ApplicationModule",
                            "metadata": {"id": "api", "version": "1.0.0"},
                            "spec": {
                                "primitive": "service",
                                "kit": "fastapi-service @ServiceFabric/reviewed/fastapi-service-1.0.0.json",
                                "source": "api",
                                "provides": [
                                    {"id": "api", "type": "http", "protocol": "http"}
                                ],
                                "lifecycle": {
                                    "readiness": {"type": "http", "path": "/health"},
                                    "shutdown": {"timeoutSeconds": 10},
                                },
                            },
                        }
                    ),
                ),
            )
        )
        self.agents = AgenticApplicationService(self.state / "agent-runs")
        self.execution = _ExecutionSpy()
        self.service = ApplicationFactoryService(
            self.state,
            blueprint_catalog=self.catalog,
            agent_service=self.agents,
            provider_execution=self.execution,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_plan_composes_profile_engineering_blueprint_and_canonical_plan(self) -> None:
        planned = self._plan()

        self.assertEqual("pending_approval", planned["status"])
        self.assertTrue(planned["technology_profile"].approved)
        self.assertEqual(
            planned["engineering_blueprint"].agent_run_plan,
            planned["plan"],
        )
        self.assertEqual(
            planned["plan"].model_dump(mode="json"),
            self.agents.store.load(planned["run_id"])["plan"],
        )
        self.assertFalse(self.repository.exists())

    def test_bootstrap_creates_exact_base_integration_and_lane_worktrees(self) -> None:
        planned = self._approved_plan()
        bootstrapped = self.service.bootstrap(planned["run_id"])

        base = bootstrapped["base_commit"]
        self.assertEqual(base, self._git(self.repository, "rev-parse", "HEAD"))
        self.assertEqual(
            base,
            self._git(Path(bootstrapped["integration_worktree"]), "rev-parse", "HEAD"),
        )
        self.assertEqual(
            {"module-api", "application-assurance"},
            set(bootstrapped["lanes"]),
        )
        for lane in bootstrapped["lanes"].values():
            self.assertEqual(base, self._git(Path(lane["worktree"]), "rev-parse", "HEAD"))
        self.assertTrue((self.repository / ".servicefabric/factory/lanes/module-api.md").is_file())
        self.assertIn("Engineering Lane: module-api", (self.repository / "api/AGENTS.md").read_text())

    def test_execute_delegates_to_wave_eight_service_with_approved_policy(self) -> None:
        planned = self._approved_plan()
        self.service.bootstrap(planned["run_id"])

        result = self.service.execute(planned["run_id"])

        self.assertEqual("pending", result["handoff"]["status"])
        self.assertEqual(planned["run_id"], self.execution.calls[0][0])
        persisted_policy = json.loads(self.execution.calls[0][1].read_text(encoding="utf-8"))
        self.assertEqual("codex", persisted_policy["default_provider"])

    def test_accepted_candidate_integrates_exact_commit_and_produces_handoff(self) -> None:
        planned = self._approved_plan()
        bootstrap = self.service.bootstrap(planned["run_id"])
        lane = Path(bootstrap["lanes"]["module-api"]["worktree"])
        candidate_path = lane / "api" / "result.txt"
        candidate_path.parent.mkdir(exist_ok=True)
        candidate_path.write_text("accepted candidate\n", encoding="utf-8")
        self._git(lane, "add", "api/result.txt")
        self._git(
            lane,
            "-c",
            "user.name=Factory Test",
            "-c",
            "user.email=factory-test@example.invalid",
            "commit",
            "-m",
            "feat: candidate",
        )
        commit_sha = self._git(lane, "rev-parse", "HEAD")
        result = AgentTaskResult(
            task_id="module-api",
            status="success",
            commit_sha=commit_sha,
            changed_paths=("api/result.txt",),
            evidence=(
                VerificationEvidence(
                    command="python3 -m unittest",
                    exit_code=0,
                    summary="verification passed",
                ),
            ),
        )
        self.agents.record_result(planned["run_id"], "module-api", result)
        reviewed = self.service.review(
            planned["run_id"],
            "module-api",
            {
                "decision_id": "review-module-api",
                "decided_by": "factory-reviewer",
                "decision": "accept",
                "reason": "Exact candidate and evidence accepted.",
            },
        )

        handoff = self.service.integrate(planned["run_id"])

        self.assertEqual("accept", reviewed.decision)
        self.assertEqual(commit_sha, reviewed.commit_sha)
        self.assertEqual("success", handoff.status)
        self.assertIsNotNone(handoff.integration_commit)
        integration = Path(bootstrap["integration_worktree"])
        self.assertEqual("accepted candidate\n", (integration / "api/result.txt").read_text())
        self.assertEqual(bootstrap["base_commit"], self._git(self.repository, "rev-parse", "HEAD"))
        self.assertEqual(handoff, self.service.handoff(planned["run_id"]))

    def _plan(self) -> dict[str, object]:
        return self.service.plan(
            intent=self.intent,
            blueprint_id="sample-blueprint",
            repository=self.repository,
            provider_policy=self.policy,
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
