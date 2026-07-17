"""Integration-owned composition of the provider-neutral agentic framework."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, is_dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
from typing import Any, Protocol

from servicefabric_agent_harness import CodexPromptHarness
from servicefabric_agent_tools import BoundedAgentTools
from servicefabric_agentic_context import ApplicationContextPack, build_context_pack
from servicefabric_agentic_contracts import (
    AgentHandoff,
    AgentRunPlan,
    AgentTask,
    AgentTaskResult,
    AgentToolResult,
    ApplicationIntent,
    VerificationEvidence,
)
from servicefabric_agentic_orchestrator import ready_tasks
from servicefabric_agentic_planner import compile_plan
from servicefabric_agentic_run_store import FileRunStore


_SAFE_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SHELL_EXECUTABLES = frozenset(
    {"bash", "cmd", "dash", "fish", "ksh", "powershell", "pwsh", "sh", "zsh"}
)
_CONTROL_TOKENS = frozenset({"&&", "||", ";", "|", ">", ">>", "<", "<<"})


class _CompletedProcess(Protocol):
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[..., _CompletedProcess]


class _WorkspaceService(Protocol):
    def inspect(self) -> object: ...

    def list_applications(self) -> tuple[object, ...]: ...

    def locate_application(self, application_id: str) -> object: ...


class _CapabilityConsumerFacade(Protocol):
    def availability_for_application(self, application_id: str) -> tuple[object, ...]: ...


class PublicServiceAgentTools:
    """Agent operations backed only by existing public ServiceFabric services."""

    def __init__(
        self,
        repository: str | Path,
        workspace_service: _WorkspaceService,
        capability_facade: _CapabilityConsumerFacade,
    ) -> None:
        self._bounded_workspace = BoundedAgentTools(repository)
        self._workspace = workspace_service
        self._capabilities = capability_facade

    def invoke(self, name: str, arguments: dict[str, Any]) -> AgentToolResult:
        if not isinstance(arguments, Mapping):
            return _tool_failed("tool arguments must be a mapping")
        if name == "workspace.inspect":
            return self._bounded_workspace.invoke(name, dict(arguments))
        if name == "workspace.status":
            if arguments:
                return _tool_failed("workspace.status accepts no arguments")
            return _tool_success("workspace status inspected", self._workspace.inspect())
        if name == "applications.list":
            if arguments:
                return _tool_failed("applications.list accepts no arguments")
            return _tool_success("applications listed", self._workspace.list_applications())
        if name == "applications.locate":
            if set(arguments) != {"application_id"}:
                return _tool_failed("applications.locate requires only application_id")
            application_id = arguments["application_id"]
            if not isinstance(application_id, str) or not application_id:
                return _tool_failed("application_id must be a non-empty string")
            return _tool_success(
                "application located",
                self._workspace.locate_application(application_id),
            )
        if name == "capabilities.discover":
            if set(arguments) != {"application_id"}:
                return _tool_failed("capabilities.discover requires only application_id")
            application_id = arguments["application_id"]
            if not isinstance(application_id, str) or not application_id:
                return _tool_failed("application_id must be a non-empty string")
            return _tool_success(
                "capabilities discovered",
                self._capabilities.availability_for_application(application_id),
            )
        return AgentToolResult(status="blocked", summary="tool is not allowlisted")


class BoundedVerificationBoundary:
    """Execute only plan-declared argv commands without a command shell."""

    def __init__(self, runner: CommandRunner = subprocess.run) -> None:
        self._runner = runner

    def run(self, command: str, repository: str | Path) -> VerificationEvidence:
        argv = self._validated_argv(command)
        try:
            completed = self._runner(
                argv,
                cwd=Path(repository),
                text=True,
                capture_output=True,
                check=False,
                timeout=300,
            )
            exit_code = completed.returncode
            summary = "verification passed" if exit_code == 0 else f"verification failed with exit code {exit_code}"
        except (OSError, subprocess.TimeoutExpired) as error:
            exit_code = 124 if isinstance(error, subprocess.TimeoutExpired) else 127
            summary = "verification timed out" if exit_code == 124 else "verification command could not be started"
        return VerificationEvidence(command=command, exit_code=exit_code, summary=summary)

    @staticmethod
    def _validated_argv(command: str) -> tuple[str, ...]:
        try:
            argv = tuple(shlex.split(command, posix=True))
        except ValueError as error:
            raise ValueError(f"invalid declared verification command: {command!r}") from error
        if not argv:
            raise ValueError("declared verification command must not be empty")
        executable = PurePosixPath(argv[0]).name.lower()
        if executable in _SHELL_EXECUTABLES or any(token in _CONTROL_TOKENS for token in argv):
            raise ValueError("declared verification command crosses the bounded verification boundary")
        return argv


class AgenticApplicationService:
    """Compose accepted Wave-7 APIs into one durable, resumable workflow."""

    def __init__(
        self,
        state_root: str | Path,
        *,
        command_runner: CommandRunner = subprocess.run,
    ) -> None:
        self.state_root = Path(state_root).expanduser().resolve()
        self.store = FileRunStore(self.state_root / "runs")
        self._runner = command_runner
        self._verification = BoundedVerificationBoundary(command_runner)

    @classmethod
    def for_current_environment(cls) -> "AgenticApplicationService":
        configured_home = os.environ.get("SERVICEFABRIC_HOME")
        root = (
            Path(configured_home).expanduser() / "agent-runs" / "wave-07"
            if configured_home
            else Path.cwd() / ".sf-agent-runtime" / "wave-07"
        )
        return cls(root)

    def plan(
        self,
        intent: ApplicationIntent,
        repository: str | Path,
        *,
        maximum_parallel_tasks: int = 1,
        tasks: Iterable[AgentTask] | None = None,
    ) -> AgentRunPlan:
        context = build_context_pack(
            repository,
            application_id=intent.application_id,
            capability_ids=intent.requested_capabilities,
        )
        compiled_tasks = tuple(tasks) if tasks is not None else (self._default_task(intent, context),)
        plan = compile_plan(
            intent,
            maximum_parallel_tasks=maximum_parallel_tasks,
            tasks=compiled_tasks,
        )
        self.store.save_plan(plan)
        metadata = {
            "version": 1,
            "run_id": plan.run_id,
            "repository": context.repository,
            "context": asdict(context),
            "tasks": {},
        }
        self._save_runtime(plan.run_id, metadata, idempotent=True)
        return plan

    def prepare(self, run_id: str, repository: str | Path) -> dict[str, object]:
        plan, _ = self._load(run_id)
        runtime = self._load_runtime(run_id)
        root = Path(repository).expanduser().resolve()
        if str(root) != runtime["repository"]:
            raise ValueError("repository does not match the execution scope recorded by plan")
        self._require_git_repository(root)
        registered_worktrees = self._registered_worktrees(root)

        prepared: list[dict[str, object]] = []
        task_metadata = runtime["tasks"]
        if not isinstance(task_metadata, dict):
            raise ValueError(f"invalid task runtime metadata for run {run_id!r}")
        for task in plan.tasks:
            target = self.state_root / "worktrees" / run_id / task.task_id
            existing = task_metadata.get(task.task_id)
            if target.exists():
                metadata_matches = isinstance(existing, dict) and existing.get("worktree") == str(target)
                interrupted_allocation = existing is None and target in registered_worktrees
                if not metadata_matches and not interrupted_allocation:
                    raise FileExistsError(f"refusing to replace existing work at {target}")
                self._require_worktree(target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                self._run_checked(
                    ("git", "-C", str(root), "worktree", "add", "--detach", str(target), "HEAD"),
                    "could not allocate task worktree",
                )

            revision = self._run_checked(
                ("git", "-C", str(target), "rev-parse", "HEAD"),
                "could not identify task worktree revision",
            ).stdout.strip()
            item = {
                "run_id": run_id,
                "task_id": task.task_id,
                "repository": str(root),
                "worktree": str(target),
                "base_revision": revision,
            }
            task_metadata[task.task_id] = item
            self._save_task_runtime(run_id, task.task_id, item)
            prepared.append(item)
        self._save_runtime(run_id, runtime)
        return {"run_id": run_id, "repository": str(root), "tasks": prepared}

    def ready(self, run_id: str) -> tuple[AgentTask, ...]:
        plan, state = self._load(run_id)
        return ready_tasks(plan, self._results(plan, state))

    def render(self, run_id: str, harness_name: str) -> dict[str, object]:
        if harness_name != "codex":
            raise ValueError("only the provider-neutral codex prompt exporter is available")
        plan, _ = self._load(run_id)
        runtime = self._load_runtime(run_id)
        task_metadata = runtime["tasks"]
        harness = CodexPromptHarness()
        rendered: list[dict[str, object]] = []
        for task in plan.tasks:
            item = task_metadata.get(task.task_id) if isinstance(task_metadata, dict) else None
            if not isinstance(item, dict) or not isinstance(item.get("worktree"), str):
                raise ValueError(f"task {task.task_id!r} must be prepared before rendering")
            task_pack = harness.prepare_task(task, item["worktree"])
            argv = ("codex", "exec", "--cd", item["worktree"], task_pack["prompt"])
            rendered.append(
                {
                    "task_pack": task_pack,
                    "launch": {"argv": argv, "command": shlex.join(argv)},
                }
            )
        return {"run_id": run_id, "harness": harness_name, "tasks": rendered}

    def status(self, run_id: str) -> dict[str, object]:
        plan, _ = self._load(run_id)
        runtime = self._load_runtime(run_id)
        return {
            "run_id": run_id,
            "plan": plan.model_dump(mode="json"),
            "ready_tasks": tuple(task.task_id for task in self.ready(run_id)),
            "prepared_tasks": tuple(sorted(runtime["tasks"])),
            "handoff": self.store.handoff(run_id).model_dump(mode="json"),
        }

    def record_result(self, run_id: str, task_id: str, result: AgentTaskResult) -> AgentTaskResult:
        plan, _ = self._load(run_id)
        tasks = {task.task_id: task for task in plan.tasks}
        if result.task_id != task_id:
            raise ValueError("result task_id does not match TASK_ID")
        if task_id not in tasks:
            raise ValueError("result task_id is not part of the run")
        task = tasks[task_id]
        self._validate_changed_paths(task, result.changed_paths)
        declared_commands = set(task.verification_commands)
        if any(item.command not in declared_commands for item in result.evidence):
            raise ValueError("result contains evidence for an undeclared verification command")
        self.store.record_result(run_id, result)
        return result

    def verify(self, run_id: str) -> dict[str, object]:
        plan, state = self._load(run_id)
        runtime = self._load_runtime(run_id)
        existing = {result.task_id: result for result in self._results(plan, state)}
        recorded: list[VerificationEvidence] = []
        failed_tasks: list[str] = []
        for task in plan.tasks:
            if not task.verification_commands:
                continue
            item = runtime["tasks"].get(task.task_id)
            if not isinstance(item, dict) or not isinstance(item.get("worktree"), str):
                raise ValueError(f"task {task.task_id!r} must be prepared before verification")
            evidence = tuple(
                self._verification.run(command, item["worktree"])
                for command in task.verification_commands
            )
            recorded.extend(evidence)
            previous = existing.get(task.task_id)
            status = "failed" if any(value.exit_code for value in evidence) else (previous.status if previous else "pending")
            if status == "failed":
                failed_tasks.append(task.task_id)
            merged_evidence = self._merge_evidence(previous.evidence if previous else (), evidence)
            self.store.record_result(
                run_id,
                AgentTaskResult(
                    task_id=task.task_id,
                    status=status,
                    changed_paths=previous.changed_paths if previous else (),
                    commit_sha=previous.commit_sha if previous else None,
                    evidence=merged_evidence,
                    blockers=previous.blockers if previous else (),
                ),
            )
        return {
            "run_id": run_id,
            "valid": not failed_tasks,
            "failed_tasks": tuple(failed_tasks),
            "evidence": tuple(item.model_dump(mode="json") for item in recorded),
        }

    def handoff(self, run_id: str) -> AgentHandoff:
        return self.store.handoff(run_id)

    @staticmethod
    def _default_task(intent: ApplicationIntent, context: ApplicationContextPack) -> AgentTask:
        return AgentTask(
            task_id=intent.intent_id,
            role="implementation",
            objective=intent.objective,
            allowed_paths=(".",),
            required_context=context.files,
            expected_outputs=("implementation",),
        )

    def _load(self, run_id: str) -> tuple[AgentRunPlan, dict[str, Any]]:
        state = self.store.load(run_id)
        return AgentRunPlan.model_validate(state["plan"]), state

    @staticmethod
    def _results(plan: AgentRunPlan, state: dict[str, Any]) -> tuple[AgentTaskResult, ...]:
        values = state["results"]
        return tuple(
            AgentTaskResult.model_validate(values[task.task_id])
            for task in plan.tasks
            if task.task_id in values
        )

    def _runtime_path(self, run_id: str) -> Path:
        self._validate_id(run_id, "run_id")
        return self.state_root / "runtime" / f"{run_id}.json"

    def _task_runtime_path(self, run_id: str, task_id: str) -> Path:
        self._validate_id(run_id, "run_id")
        self._validate_id(task_id, "task_id")
        return self.state_root / "runtime" / run_id / f"{task_id}.json"

    def _load_runtime(self, run_id: str) -> dict[str, Any]:
        value = json.loads(self._runtime_path(run_id).read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("run_id") != run_id:
            raise ValueError(f"invalid runtime metadata for run {run_id!r}")
        if set(value) != {"version", "run_id", "repository", "context", "tasks"}:
            raise ValueError(f"invalid runtime metadata shape for run {run_id!r}")
        return value

    def _save_runtime(self, run_id: str, value: dict[str, Any], *, idempotent: bool = False) -> None:
        target = self._runtime_path(run_id)
        if idempotent and target.exists():
            existing = self._load_runtime(run_id)
            expected = dict(value)
            expected["tasks"] = existing["tasks"]
            if existing != expected:
                raise ValueError(f"run {run_id!r} already has different runtime metadata")
            return
        self._atomic_json(target, value)

    def _save_task_runtime(self, run_id: str, task_id: str, value: dict[str, Any]) -> None:
        target = self._task_runtime_path(run_id, task_id)
        if target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
            if existing != value:
                raise ValueError(f"task {task_id!r} already has different runtime metadata")
            return
        self._atomic_json(target, value)

    @staticmethod
    def _atomic_json(target: Path, value: object) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        try:
            temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    def _require_git_repository(self, repository: Path) -> None:
        completed = self._run_checked(
            ("git", "-C", str(repository), "rev-parse", "--show-toplevel"),
            "repository is not a Git worktree",
        )
        if Path(completed.stdout.strip()).resolve() != repository:
            raise ValueError("repository must be the root of a Git worktree")

    def _require_worktree(self, worktree: Path) -> None:
        completed = self._run_checked(
            ("git", "-C", str(worktree), "rev-parse", "--is-inside-work-tree"),
            "recorded task worktree is invalid",
        )
        if completed.stdout.strip() != "true":
            raise ValueError(f"recorded task worktree is invalid: {worktree}")

    def _registered_worktrees(self, repository: Path) -> set[Path]:
        completed = self._run_checked(
            ("git", "-C", str(repository), "worktree", "list", "--porcelain"),
            "could not inspect repository worktrees",
        )
        return {
            Path(line.removeprefix("worktree ")).resolve()
            for line in completed.stdout.splitlines()
            if line.startswith("worktree ")
        }

    def _run_checked(self, argv: tuple[str, ...], message: str) -> _CompletedProcess:
        completed = self._runner(argv, text=True, capture_output=True, check=False)
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise ValueError(f"{message}: {detail}" if detail else message)
        return completed

    @staticmethod
    def _validate_changed_paths(task: AgentTask, paths: tuple[str, ...]) -> None:
        for path in paths:
            candidate = PurePosixPath(path)
            if not path or path.startswith("/") or "\\" in path or ".." in candidate.parts:
                raise ValueError(f"result contains unsafe changed path {path!r}")
            if not any(_path_is_within(path, allowed) for allowed in task.allowed_paths):
                raise ValueError(f"changed path {path!r} is outside task ownership")
            if any(_path_is_within(path, forbidden) for forbidden in task.forbidden_paths):
                raise ValueError(f"changed path {path!r} is forbidden for task {task.task_id!r}")

    @staticmethod
    def _merge_evidence(
        existing: tuple[VerificationEvidence, ...],
        current: tuple[VerificationEvidence, ...],
    ) -> tuple[VerificationEvidence, ...]:
        replacements = {item.command: item for item in current}
        merged = [item for item in existing if item.command not in replacements]
        merged.extend(current)
        return tuple(merged)

    @staticmethod
    def _validate_id(value: str, name: str) -> None:
        if not _SAFE_ID.fullmatch(value):
            raise ValueError(f"invalid {name}: {value!r}")


def _path_is_within(path: str, boundary: str) -> bool:
    if boundary == ".":
        return True
    normalized = boundary.rstrip("/")
    return path == normalized or path.startswith(normalized + "/")


def _json_value(value: object) -> object:
    if hasattr(value, "model_dump"):
        return _json_value(value.model_dump(mode="json"))
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _tool_success(summary: str, value: object) -> AgentToolResult:
    return AgentToolResult(status="success", summary=summary, data={"value": _json_value(value)})


def _tool_failed(summary: str) -> AgentToolResult:
    return AgentToolResult(status="failed", summary=summary)


def dispatch_agents(args: object) -> tuple[int, str, object]:
    """Compatibility dispatcher retained while the CLI surface is composed."""

    service = AgenticApplicationService.for_current_environment()
    command = getattr(args, "agents_action")
    if command == "providers":
        from .agent_providers import ProviderRegistry

        registry = ProviderRegistry()
        if getattr(args, "provider_action") == "list":
            return 0, "agents-providers-list", {"providers": registry.list()}
        return 0, "agents-providers-doctor", {
            "providers": registry.doctor(getattr(args, "provider", None)),
        }
    if command in {"execute", "events", "resume", "cancel"}:
        # These commands intentionally retain the public CLI contract before the
        # runtime and LangGraph specialist packages are composed into this branch.
        raise ValueError("Wave-8 provider runtime composition is not installed")
    if command == "plan":
        raw = json.loads(Path(getattr(args, "intent")).read_text(encoding="utf-8"))
        intent = ApplicationIntent.model_validate(raw)
        repository = Path.cwd().resolve()
        plan = service.plan(
            intent,
            repository,
            maximum_parallel_tasks=getattr(args, "maximum_parallel_tasks", 1),
        )
        return 0, "agents-plan", plan.model_dump(mode="json")
    run_id = getattr(args, "run_id")
    if command == "prepare":
        return 0, "agents-prepare", service.prepare(run_id, getattr(args, "repository"))
    if command == "ready":
        return 0, "agents-ready", {
            "run_id": run_id,
            "tasks": tuple(task.model_dump(mode="json") for task in service.ready(run_id)),
        }
    if command == "render":
        return 0, "agents-render", service.render(run_id, getattr(args, "harness"))
    if command == "status":
        return 0, "agents-status", service.status(run_id)
    if command == "record-result":
        raw = json.loads(Path(getattr(args, "result")).read_text(encoding="utf-8"))
        result = AgentTaskResult.model_validate(raw)
        recorded = service.record_result(run_id, getattr(args, "task_id"), result)
        return 0, "agents-record-result", recorded.model_dump(mode="json")
    if command == "verify":
        result = service.verify(run_id)
        return (0 if result["valid"] else 1), "agents-verify", result
    if command == "handoff":
        return 0, "agents-handoff", service.handoff(run_id).model_dump(mode="json")
    raise ValueError(f"unsupported agents command: {command}")
