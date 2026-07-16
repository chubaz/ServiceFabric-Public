from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from servicefabric_agentic_contracts import AgentTask, AgentTaskResult, ApplicationIntent
from servicefabric_client.agentic import AgenticApplicationService, PublicServiceAgentTools
from servicefabric_client.main import dispatch


class AgenticCompositionTests(unittest.TestCase):
    def _repository(self, root: Path) -> Path:
        repository = root / "repository"
        repository.mkdir()
        (repository / "AGENTS.md").write_text("# Bounded agent instructions\n", encoding="utf-8")
        (repository / "verify_task.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        subprocess.run(("git", "init", "-q", str(repository)), check=True)
        subprocess.run(("git", "-C", str(repository), "add", "."), check=True)
        subprocess.run(
            (
                "git", "-C", str(repository), "-c", "user.name=ServiceFabric",
                "-c", "user.email=servicefabric@example.invalid", "commit", "-qm", "initial",
            ),
            check=True,
        )
        return repository

    def test_plan_prepare_and_render_are_bounded_and_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self._repository(root)
            commands: list[tuple[str, ...]] = []

            def runner(argv, **kwargs):
                commands.append(tuple(argv))
                return subprocess.run(argv, **kwargs)

            service = AgenticApplicationService(root / "state", command_runner=runner)
            intent = ApplicationIntent(
                intent_id="compose",
                mode="create",
                objective="Compose the application",
                requested_capabilities=("search", "search"),
            )
            plan = service.plan(intent, repository)
            self.assertEqual(plan.tasks[0].required_context, ("AGENTS.md",))

            first = service.prepare(plan.run_id, repository)
            second = service.prepare(plan.run_id, repository)
            self.assertEqual(first, second)
            task_runtime = root / "state" / "runtime" / plan.run_id / "compose.json"
            self.assertTrue(task_runtime.is_file())

            rendered = service.render(plan.run_id, "codex")
            item = rendered["tasks"][0]
            self.assertEqual(set(item["task_pack"]), {"task_id", "repository", "prompt"})
            self.assertEqual(item["launch"]["argv"][:3], ("codex", "exec", "--cd"))
            self.assertEqual(item["launch"]["argv"][-1], item["task_pack"]["prompt"])
            self.assertNotIn("codex", {argv[0] for argv in commands})

            resumed = AgenticApplicationService(root / "state")
            self.assertEqual(resumed.status(plan.run_id)["prepared_tasks"], ("compose",))

    def test_ready_results_and_handoff_follow_dependencies_and_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self._repository(root)
            service = AgenticApplicationService(root / "state")
            intent = ApplicationIntent(intent_id="graph", mode="modify", objective="Run graph")
            tasks = (
                AgentTask(task_id="prepare", role="planner", objective="Prepare", allowed_paths=("docs",)),
                AgentTask(task_id="implement", role="implementation", objective="Implement", dependencies=("prepare",), allowed_paths=("src",)),
                AgentTask(task_id="inspect", role="review", objective="Inspect", allowed_paths=("tests",)),
            )
            plan = service.plan(intent, repository, maximum_parallel_tasks=2, tasks=tasks)
            self.assertEqual(tuple(task.task_id for task in service.ready(plan.run_id)), ("prepare", "inspect"))

            with self.assertRaisesRegex(ValueError, "outside task ownership"):
                service.record_result(
                    plan.run_id,
                    "prepare",
                    AgentTaskResult(task_id="prepare", status="success", changed_paths=("src/oops.py",)),
                )
            service.record_result(
                plan.run_id,
                "prepare",
                AgentTaskResult(task_id="prepare", status="success", changed_paths=("docs/plan.md",)),
            )
            self.assertEqual(tuple(task.task_id for task in service.ready(plan.run_id)), ("implement", "inspect"))
            service.record_result(plan.run_id, "implement", AgentTaskResult(task_id="implement", status="blocked", blockers=("review required",)))

            resumed = AgenticApplicationService(root / "state")
            handoff = resumed.handoff(plan.run_id)
            self.assertEqual(handoff.status, "blocked")
            self.assertEqual(handoff.unresolved_blockers, ("review required",))

    def test_verification_and_agent_tools_stay_behind_public_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self._repository(root)
            service = AgenticApplicationService(root / "state")
            intent = ApplicationIntent(intent_id="verify", mode="debug", objective="Verify")
            task = AgentTask(
                task_id="verify",
                role="verification",
                objective="Verify",
                allowed_paths=(".",),
                verification_commands=("python3 verify_task.py",),
            )
            plan = service.plan(intent, repository, tasks=(task,))
            service.prepare(plan.run_id, repository)
            service.record_result(plan.run_id, "verify", AgentTaskResult(task_id="verify", status="success"))
            result = service.verify(plan.run_id)
            self.assertTrue(result["valid"])
            self.assertEqual(result["evidence"][0]["command"], "python3 verify_task.py")
            self.assertEqual(service.handoff(plan.run_id).task_results[0].evidence[0].exit_code, 0)

            shell_intent = ApplicationIntent(intent_id="shell", mode="debug", objective="Reject shell")
            shell_task = AgentTask(task_id="shell", role="verification", objective="Reject", allowed_paths=(".",), verification_commands=("sh -c true",))
            shell_plan = service.plan(shell_intent, repository, tasks=(shell_task,))
            service.prepare(shell_plan.run_id, repository)
            with self.assertRaisesRegex(ValueError, "bounded verification boundary"):
                service.verify(shell_plan.run_id)

            class Workspace:
                def inspect(self): return {"state": "ready"}
                def list_applications(self): return ("app",)
                def locate_application(self, application_id): return {"id": application_id}

            class Capabilities:
                def availability_for_application(self, application_id): return ({"application_id": application_id},)

            tools = PublicServiceAgentTools(repository, Workspace(), Capabilities())
            self.assertEqual(tools.invoke("workspace.status", {}).status, "success")
            self.assertEqual(tools.invoke("applications.list", {}).status, "success")
            self.assertEqual(tools.invoke("capabilities.discover", {"application_id": "app"}).status, "success")
            self.assertEqual(tools.invoke("shell.execute", {"command": "true"}).status, "blocked")

    def test_cli_exposes_the_resumable_agentic_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = self._repository(root)
            intent_path = repository / "intent.json"
            intent_path.write_text(
                json.dumps(
                    {
                        "intent_id": "cli",
                        "mode": "create",
                        "objective": "Compose through the CLI",
                    }
                ),
                encoding="utf-8",
            )
            result_path = repository / "result.json"
            result_path.write_text(
                json.dumps({"task_id": "cli", "status": "success"}),
                encoding="utf-8",
            )

            previous = Path.cwd()
            try:
                os.chdir(repository)
                with patch.dict(os.environ, {"SERVICEFABRIC_HOME": str(root / "state")}):
                    code, _, plan = dispatch(("agents", "plan", "--intent", str(intent_path)))
                    self.assertEqual(code, 0)
                    run_id = plan["run_id"]
                    self.assertEqual(run_id, "run-cli")
                    self.assertEqual(dispatch(("agents", "ready", run_id))[2]["tasks"][0]["task_id"], "cli")
                    prepared = dispatch(("agents", "prepare", run_id, "--repository", str(repository)))[2]
                    self.assertEqual(prepared["tasks"][0]["task_id"], "cli")
                    rendered = dispatch(("agents", "render", run_id, "--harness", "codex"))[2]
                    self.assertEqual(set(rendered["tasks"][0]["task_pack"]), {"task_id", "repository", "prompt"})
                    self.assertTrue(rendered["tasks"][0]["launch"]["command"].startswith("codex exec --cd "))
                    self.assertEqual(dispatch(("agents", "status", run_id))[2]["handoff"]["status"], "pending")
                    dispatch(("agents", "record-result", run_id, "cli", "--result", str(result_path)))
                    self.assertTrue(dispatch(("agents", "verify", run_id))[2]["valid"])
                    self.assertEqual(dispatch(("agents", "handoff", run_id))[2]["status"], "success")
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
