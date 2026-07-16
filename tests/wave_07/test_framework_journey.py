"""One black-box acceptance journey for the complete Wave-7 agentic workflow."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "wave_07"
for source_root in reversed(
    (
        "packages/servicefabric_agentic_contracts/src",
        "packages/servicefabric_agentic_context/src",
        "packages/servicefabric_agentic_planner/src",
        "packages/servicefabric_agentic_run_store/src",
        "packages/servicefabric_agent_tools/src",
        "packages/servicefabric_agentic_orchestrator/src",
        "packages/servicefabric_agent_harness/src",
        "clients/python",
    )
):
    sys.path.insert(0, str(REPOSITORY_ROOT / source_root))


from servicefabric_agentic_context import build_context_pack
from servicefabric_agentic_contracts import AgentTask, AgentTaskResult, ApplicationIntent
from servicefabric_agentic_planner import compile_plan
from servicefabric_blueprints import create_default_blueprint_catalog
from servicefabric_client.agentic import AgenticApplicationService, PublicServiceAgentTools
from servicefabric_client.capability_projections import CapabilityProjectionComposition
from servicefabric_client.main import dispatch
from servicefabric_framework_kits import get_default_catalog
from servicefabric_application_model import VALID_PRIMITIVES
from servicefabric_workspace import resolve_workspace


class Wave07BlackBoxJourneyTests(unittest.TestCase):
    def test_single_intent_to_resumed_evidenced_handoff_and_capability_inventory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="servicefabric-wave7-evaluation-") as temporary:
            root = Path(temporary)
            repository = self._create_repository(root)
            workspace = root / "workspace"

            intent = ApplicationIntent.model_validate_json(
                (FIXTURES_ROOT / "application_intent.json").read_text(encoding="utf-8")
            )
            self.assertEqual(intent.intent_id, "wave7-journey")

            with patch.dict(
                os.environ,
                {"SERVICEFABRIC_WORKSPACE": str(workspace)},
                clear=False,
            ):
                os.environ.pop("SERVICEFABRIC_HOME", None)
                self._call_cli("workspace", "init", str(workspace))
                self._call_cli("apps", "create", "research-notes", "--template", "modular-web-app")
                self._call_cli("capabilities", "register", "research-notes")

            composition = CapabilityProjectionComposition.for_workspace(
                resolve_workspace(explicit_workspace=workspace).layout
            )
            registered_capabilities = tuple(
                item.capability_id
                for item in composition.facade.list_capabilities("research-notes")
            )
            context = build_context_pack(
                repository,
                application_id=intent.application_id,
                capability_ids=registered_capabilities,
            )
            blueprint_ids = tuple(
                item.blueprint_id for item in create_default_blueprint_catalog().list()
            )
            kit_ids = tuple(
                sorted(
                    {
                        item.reference.kit_id
                        for primitive in VALID_PRIMITIVES
                        for item in get_default_catalog().list_for_primitive(primitive)
                    }
                )
            )
            context_inventory = {
                "workspace": context.files,
                "blueprints": blueprint_ids,
                "kits": kit_ids,
                "capabilities": context.capability_ids,
            }
            self.assertEqual(
                context_inventory,
                {
                    "workspace": (
                        "AGENTS.md",
                        "workspace.yaml",
                        "README.md",
                        "docs/architecture/specification-map.md",
                    ),
                    "blueprints": ("research-notes", "text-utility"),
                    "kits": ("fastapi-service", "python-library", "react-web"),
                    "capabilities": ("notes.create", "notes.get", "notes.search"),
                },
            )
            self.assertEqual(context.capability_ids, intent.requested_capabilities)

            tasks = (
                AgentTask(
                    task_id="foundation",
                    role="planner",
                    objective="Prepare the deterministic implementation plan",
                    allowed_paths=("docs",),
                    required_context=context.files,
                    expected_outputs=("docs/plan.md",),
                    verification_commands=("python3 verify_task.py",),
                ),
                AgentTask(
                    task_id="risk-review",
                    role="review",
                    objective="Review capability integration risks",
                    allowed_paths=("tests",),
                    required_context=("AGENTS.md",),
                    expected_outputs=("tests/risk-review.md",),
                ),
                AgentTask(
                    task_id="implement",
                    role="implementation",
                    objective="Implement the approved plan",
                    dependencies=("foundation",),
                    allowed_paths=("src",),
                    required_context=("AGENTS.md", "docs/plan.md"),
                    expected_outputs=("src/application.py",),
                ),
                AgentTask(
                    task_id="release",
                    role="release",
                    objective="Assemble the verified release",
                    dependencies=("implement", "risk-review"),
                    allowed_paths=("dist",),
                    required_context=("docs/plan.md",),
                    expected_outputs=("dist/release.json",),
                ),
            )

            commands: list[tuple[str, ...]] = []

            def recording_runner(argv: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[str]:
                commands.append(tuple(argv))
                return subprocess.run(argv, **kwargs)

            state_root = root / "state"
            service = AgenticApplicationService(state_root, command_runner=recording_runner)
            plan = service.plan(
                intent,
                repository,
                maximum_parallel_tasks=2,
                tasks=tasks,
            )
            self.assertEqual(
                plan,
                compile_plan(intent, maximum_parallel_tasks=2, tasks=tasks),
            )
            self.assertEqual(
                compile_plan(intent, maximum_parallel_tasks=2, tasks=tasks),
                compile_plan(intent, maximum_parallel_tasks=2, tasks=tasks),
            )
            self.assertEqual(
                tuple(task.task_id for task in service.ready(plan.run_id)),
                ("foundation", "risk-review"),
            )

            prepared = service.prepare(plan.run_id, repository)
            self.assertEqual(prepared, service.prepare(plan.run_id, repository))
            worktrees = tuple(Path(item["worktree"]) for item in prepared["tasks"])
            self.assertEqual(len(set(worktrees)), len(tasks))
            for item, worktree in zip(prepared["tasks"], worktrees, strict=True):
                self.assertTrue(worktree.is_relative_to(state_root / "worktrees" / plan.run_id))
                self.assertEqual(item["base_revision"], self._git(repository, "rev-parse", "HEAD"))
                self.assertEqual(self._git(worktree, "rev-parse", "--is-inside-work-tree"), "true")

            rendered = service.render(plan.run_id, "codex")
            self.assertEqual(len(rendered["tasks"]), len(tasks))
            self.assertEqual(
                rendered["tasks"][0]["task_pack"]["prompt"],
                (FIXTURES_ROOT / "codex_prompt.txt").read_text(encoding="utf-8"),
            )
            for task, rendered_item, worktree in zip(tasks, rendered["tasks"], worktrees, strict=True):
                task_pack = rendered_item["task_pack"]
                self.assertEqual(set(task_pack), {"task_id", "repository", "prompt"})
                self.assertEqual(task_pack["task_id"], task.task_id)
                self.assertEqual(task_pack["repository"], str(worktree))
                self.assertEqual(rendered_item["launch"]["argv"][:3], ("codex", "exec", "--cd"))
            self.assertNotIn("codex", {argv[0] for argv in commands})

            # Dropping the service simulates interruption; a new instance resumes
            # solely from the run store and runtime metadata on disk.
            del service
            resumed = AgenticApplicationService(state_root, command_runner=recording_runner)
            status = resumed.status(plan.run_id)
            self.assertEqual(
                status["prepared_tasks"],
                tuple(sorted(task.task_id for task in tasks)),
            )
            self.assertEqual(status["handoff"]["status"], "pending")

            resumed.record_result(
                plan.run_id,
                "risk-review",
                AgentTaskResult(task_id="risk-review", status="running"),
            )
            resumed.record_result(
                plan.run_id,
                "foundation",
                AgentTaskResult(
                    task_id="foundation",
                    status="success",
                    changed_paths=("docs/plan.md",),
                ),
            )
            self.assertEqual(
                tuple(task.task_id for task in resumed.ready(plan.run_id)),
                ("implement",),
            )

            resumed.record_result(
                plan.run_id,
                "risk-review",
                AgentTaskResult(
                    task_id="risk-review",
                    status="failed",
                    blockers=("capability review failed",),
                ),
            )
            resumed.record_result(
                plan.run_id,
                "implement",
                AgentTaskResult(
                    task_id="implement",
                    status="success",
                    changed_paths=("src/application.py",),
                ),
            )
            self.assertEqual(resumed.ready(plan.run_id), ())

            verification = resumed.verify(plan.run_id)
            self.assertTrue(verification["valid"])
            self.assertEqual(
                verification["evidence"],
                (
                    {
                        "command": "python3 verify_task.py",
                        "exit_code": 0,
                        "summary": "verification passed",
                        "artifact_ref": None,
                    },
                ),
            )

            class UnusedWorkspaceService:
                pass

            tools = PublicServiceAgentTools(
                repository,
                UnusedWorkspaceService(),
                composition.facade,
            )
            discovered = tools.invoke(
                "capabilities.discover",
                {"application_id": "research-notes"},
            )
            self.assertEqual(discovered.status, "success")
            self.assertEqual(
                tuple(item["capability_id"] for item in discovered.data["value"]),
                registered_capabilities,
            )

            expected_handoff = json.loads(
                (FIXTURES_ROOT / "expected_handoff.json").read_text(encoding="utf-8")
            )
            durable_handoff = AgenticApplicationService(state_root).handoff(plan.run_id)
            self.assertEqual(durable_handoff.model_dump(mode="json"), expected_handoff)
            self.assertEqual(
                AgenticApplicationService(state_root).handoff(plan.run_id),
                durable_handoff,
            )

    def _create_repository(self, root: Path) -> Path:
        repository = root / "repository"
        (repository / "docs" / "architecture").mkdir(parents=True)
        (repository / "AGENTS.md").write_text("# Bounded agent policy\n", encoding="utf-8")
        (repository / "workspace.yaml").write_text("workspace: evaluation\n", encoding="utf-8")
        (repository / "README.md").write_text("# Wave-7 evaluation\n", encoding="utf-8")
        (repository / "docs" / "architecture" / "specification-map.md").write_text(
            "# Specification map\n",
            encoding="utf-8",
        )
        (repository / "verify_task.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        subprocess.run(("git", "init", "-q", str(repository)), check=True)
        subprocess.run(("git", "-C", str(repository), "add", "."), check=True)
        subprocess.run(
            (
                "git",
                "-C",
                str(repository),
                "-c",
                "user.name=ServiceFabric",
                "-c",
                "user.email=servicefabric@example.invalid",
                "commit",
                "-qm",
                "initial fixture",
            ),
            check=True,
        )
        return repository

    def _call_cli(self, *arguments: str) -> object:
        code, _, value = dispatch(arguments)
        self.assertEqual(code, 0, (arguments, value))
        return value

    @staticmethod
    def _git(repository: Path, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()


if __name__ == "__main__":
    unittest.main()
