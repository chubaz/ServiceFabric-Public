"""Application-factory composition over the accepted Wave-3/7/8/9 APIs."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Protocol

from servicefabric_agent_provider_contracts import ProviderPolicy
from servicefabric_agentic_contracts import AgentRunPlan, AgentTaskResult, ApplicationIntent
from servicefabric_application_candidate_review import CandidateReviewService
from servicefabric_application_factory_bootstrap import RepositoryBootstrap, WorktreeSpec
from servicefabric_application_factory_contracts import (
    ApplicationFactoryHandoff,
    CandidateReviewDecision,
    EngineeringBlueprint,
    FactoryApprovalDecision,
    TechnologyProfile,
    UnmetRequirement,
)
from servicefabric_application_factory_state import FileFactoryLifecycleStore
from servicefabric_application_generator import ApplicationGenerator, GenerationRequest
from servicefabric_application_integration import (
    ApplicationIntegrationRequest,
    ApplicationIntegrationService,
    VerificationOutcome,
)
from servicefabric_blueprints import (
    ApplicationBlueprint,
    BlueprintCatalog,
    create_default_blueprint_catalog,
)
from servicefabric_engineering_blueprints import compile_engineering_blueprint
from servicefabric_technology_profiles import TechnologyProfileRequest, TechnologyProfileSelector

from .agent_providers import default_provider_registry, load_provider_policy
from .agentic import AgenticApplicationService, BoundedVerificationBoundary
from .provider_execution import ProviderExecutionService


_LOCAL_RESOURCE_TYPES = frozenset(
    {
        "file-system",
        "filesystem",
        "http-endpoint",
        "loopback",
        "relational-database",
        "sqlite",
        "web-endpoint",
    }
)


class FactoryStateError(ValueError):
    """Raised when a factory command is invalid for the durable run state."""


class _ProviderExecution(Protocol):
    def execute(self, run_id: str, policy_path: str | Path) -> dict[str, object]: ...

    def events(self, run_id: str, task_id: str | None = None) -> tuple[dict[str, object], ...]: ...

    def usage(self, run_id: str) -> tuple[dict[str, object], ...]: ...


class GitIntegrationRepository:
    """Non-destructive local-Git adapter for ``ApplicationIntegrationService``."""

    def __init__(self, repository: str | Path) -> None:
        self.repository = Path(repository).resolve()
        self._verification = BoundedVerificationBoundary()

    def is_clean(self) -> bool:
        return not self._git("status", "--porcelain").strip()

    def current_branch(self) -> str:
        return self._git("branch", "--show-current").strip()

    def head_sha(self) -> str:
        return self._git("rev-parse", "HEAD").strip()

    def commit_exists(self, commit_sha: str) -> bool:
        return self._git_ok("cat-file", "-e", f"{commit_sha}^{{commit}}")

    def changed_paths(self, commit_sha: str, base_sha: str) -> tuple[str, ...]:
        output = self._git("diff", "--name-only", base_sha, commit_sha)
        return tuple(path for path in output.splitlines() if path)

    def is_ancestor(self, ancestor_sha: str, descendant_sha: str) -> bool:
        return self._git_ok("merge-base", "--is-ancestor", ancestor_sha, descendant_sha)

    def is_already_integrated(self, commit_sha: str) -> bool:
        return self.is_ancestor(commit_sha, "HEAD")

    def cherry_pick_exact(self, *, commit_sha: str, target_branch: str) -> str:
        if self.current_branch() != target_branch:
            raise FactoryStateError("integration worktree left its approved branch")
        self._git(
            "-c",
            "user.name=ServiceFabric Factory",
            "-c",
            "user.email=factory@servicefabric.invalid",
            "cherry-pick",
            commit_sha,
        )
        return self.head_sha()

    def integration_commit(self, *, target_branch: str) -> str:
        if self.current_branch() != target_branch:
            raise FactoryStateError("integration worktree left its approved branch")
        self._git(
            "-c",
            "user.name=ServiceFabric Factory",
            "-c",
            "user.email=factory@servicefabric.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "chore(factory): record accepted application integration",
        )
        return self.head_sha()

    def run_verification(self, commands: tuple[str, ...]) -> VerificationOutcome:
        evidence: list[str] = []
        succeeded = True
        for index, command in enumerate(commands, start=1):
            result = self._verification.run(command, self.repository)
            evidence.append(
                f"verification:{index}:{result.exit_code}:{hashlib.sha256(command.encode()).hexdigest()}"
            )
            succeeded = succeeded and result.exit_code == 0
        return VerificationOutcome(succeeded=succeeded, evidence_refs=tuple(evidence))

    def _git_ok(self, *arguments: str) -> bool:
        completed = subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.returncode == 0

    def _git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown Git error"
            raise FactoryStateError(f"git {' '.join(arguments)} failed: {detail}")
        return completed.stdout


class ApplicationFactoryService:
    """Compose reviewed packages without owning provider or specialist behavior."""

    def __init__(
        self,
        state_root: str | Path,
        *,
        blueprint_catalog: BlueprintCatalog | None = None,
        generator: ApplicationGenerator | None = None,
        agent_service: AgenticApplicationService | None = None,
        provider_execution: _ProviderExecution | None = None,
        resource_resolver: Callable[[object], bool] | None = None,
    ) -> None:
        self.state_root = Path(state_root).expanduser().resolve()
        self._catalog = blueprint_catalog or create_default_blueprint_catalog()
        self._generator = generator or ApplicationGenerator()
        self._agents = agent_service or AgenticApplicationService(self.state_root / "agent-runs")
        self._provider_execution = provider_execution
        self._resources = resource_resolver or (
            lambda request: getattr(request, "scope", None) == "application"
            and getattr(request, "type", None) in _LOCAL_RESOURCE_TYPES
        )
        self._lifecycle = FileFactoryLifecycleStore(self.state_root / "lifecycle")
        self._review = CandidateReviewService()
        self._integration = ApplicationIntegrationService()

    @classmethod
    def for_current_environment(cls) -> "ApplicationFactoryService":
        configured = os.environ.get("SERVICEFABRIC_HOME")
        root = (
            Path(configured).expanduser() / "factory-runs" / "wave-09"
            if configured
            else Path.cwd() / ".sf-agent-runtime" / "wave-09"
        )
        return cls(root)

    def plan(
        self,
        *,
        intent: ApplicationIntent | str | Path,
        blueprint_id: str,
        repository: str | Path,
        provider_policy: ProviderPolicy | str | Path,
    ) -> dict[str, object]:
        loaded_intent = self._load_intent(intent)
        run_id = f"run-{loaded_intent.intent_id}"
        application_id = loaded_intent.application_id or blueprint_id
        repository_path = Path(repository).expanduser().resolve()

        try:
            blueprint = self._resolve_blueprint(blueprint_id)
            policy = self._load_policy(provider_policy)
            unmet = self._selection_unmet(run_id, application_id, loaded_intent, blueprint)
            if unmet:
                return self._blocked_plan(
                    run_id, application_id, repository_path, loaded_intent, blueprint, unmet
                )

            modules = blueprint.load_modules()
            lifecycle = {
                module.module_id: self._required_lifecycle(str(module.primitive))
                for module in modules
            }
            profile = TechnologyProfileSelector(policy).select(
                TechnologyProfileRequest(
                    profile_id=f"profile-{loaded_intent.intent_id}",
                    intent=loaded_intent,
                    blueprint=blueprint,
                    lifecycle_requirements=lifecycle,
                    provider_roles={module.module_id: "implementation" for module in modules},
                )
            )
            if profile.unresolved_requirements or not profile.approved:
                unmet = tuple(
                    self._unmet(
                        run_id,
                        application_id,
                        f"technology-{item}",
                        f"Technology profile requirement is unresolved: {item}.",
                        "framework-kit" if item.startswith(("kit-", "lifecycle-")) else "primitive",
                    )
                    for item in profile.unresolved_requirements
                )
                return self._blocked_plan(
                    run_id,
                    application_id,
                    repository_path,
                    loaded_intent,
                    blueprint,
                    unmet,
                    profile=profile,
                )

            engineering = compile_engineering_blueprint(
                loaded_intent,
                blueprint,
                profile,
                run_id=run_id,
                maximum_parallel_tasks=policy.maximum_parallel_per_provider,
            )
        except Exception as error:
            unmet = (
                self._unmet(
                    run_id,
                    application_id,
                    "reviewed-technology",
                    str(error),
                    "framework-kit",
                ),
            )
            return self._blocked_plan(
                run_id, application_id, repository_path, loaded_intent, None, unmet
            )

        self._agents.store.save_plan(engineering.agent_run_plan)
        policy_path = self._artifact_path(run_id, "provider-policy.json")
        self._atomic_json(policy_path, policy.model_dump(mode="json"))
        approval_payload = {
            "application_blueprint_id": blueprint.blueprint_id,
            "application_blueprint_version": blueprint.version,
            "technology_profile": profile.model_dump(mode="json"),
            "engineering_blueprint": engineering.model_dump(mode="json"),
            "provider_policy": policy.model_dump(mode="json"),
        }
        subject_ref = f"factory-plan:{run_id}:{self._digest(approval_payload)}"
        record = {
            "version": 1,
            "run_id": run_id,
            "application_id": application_id,
            "repository": str(repository_path),
            "intent": loaded_intent.model_dump(mode="json"),
            "application_blueprint_id": blueprint.blueprint_id,
            "application_blueprint_version": blueprint.version,
            "technology_profile": profile.model_dump(mode="json"),
            "engineering_blueprint": engineering.model_dump(mode="json"),
            "provider_policy_path": str(policy_path),
            "approval_subject_ref": subject_ref,
            "planning_state": "pending_approval",
            "bootstrap": None,
        }
        self._write_record(run_id, record, create=True)
        return {
            "run_id": run_id,
            "status": "pending_approval",
            "application_blueprint": {
                "blueprint_id": blueprint.blueprint_id,
                "version": blueprint.version,
            },
            "technology_profile": profile,
            "engineering_blueprint": engineering,
            "plan": engineering.agent_run_plan,
            "approval_subject_ref": subject_ref,
            "repository_created": False,
            "unmet_requirements": (),
        }

    def approve(
        self, run_id: str, decision: FactoryApprovalDecision | str | Path
    ) -> FactoryApprovalDecision:
        record = self._load_record(run_id)
        loaded = self._load_contract(decision, FactoryApprovalDecision)
        if loaded.run_id != run_id:
            raise FactoryStateError("approval decision belongs to a different factory run")
        if loaded.subject_ref != record.get("approval_subject_ref"):
            raise FactoryStateError("approval decision does not name the exact pending profile and blueprint")
        snapshot = self._snapshot(run_id)
        if snapshot.approvals and loaded not in snapshot.approvals:
            raise FactoryStateError("the pending profile and blueprint already have a decision")
        self._lifecycle.record_approval(loaded)
        return loaded

    def bootstrap(self, run_id: str) -> dict[str, object]:
        record = self._approved_record(run_id)
        if record.get("bootstrap") is not None:
            raise FactoryStateError("factory run is already bootstrapped")
        blueprint = self._blueprint_from_record(record)
        profile = TechnologyProfile.model_validate(record["technology_profile"])
        engineering = EngineeringBlueprint.model_validate(record["engineering_blueprint"])
        repository = Path(str(record["repository"]))
        self._materialize(repository, str(record["application_id"]), blueprint)
        self._write_guidance(repository, profile, engineering)
        base_commit = self._initialize_base(repository, run_id)

        worktree_root = self.state_root / "worktrees" / run_id
        worktree_root.mkdir(parents=True, exist_ok=False)
        integration_lane = next(lane for lane in engineering.lanes if lane.integration_owned)
        integration = WorktreeSpec(
            branch=f"factory/{run_id}/integration",
            path=worktree_root / "integration",
        )
        candidate_lanes = tuple(lane for lane in engineering.lanes if lane != integration_lane)
        lane_specs = tuple(
            WorktreeSpec(
                branch=f"factory/{run_id}/lane/{lane.lane_id}",
                path=worktree_root / lane.lane_id,
            )
            for lane in candidate_lanes
        )
        result = RepositoryBootstrap(repository).create_worktrees(
            base_commit=base_commit,
            integration=integration,
            lanes=lane_specs,
        )

        self._agents.plan(
            engineering.agent_run_plan.intent,
            result.integration.path,
            maximum_parallel_tasks=engineering.maximum_parallel_tasks,
            tasks=engineering.agent_run_plan.tasks,
        )
        bootstrap = {
            "base_commit": result.repository.base_commit,
            "integration_branch": result.integration.branch,
            "integration_worktree": str(result.integration.path),
            "lanes": {
                lane.lane_id: {
                    "branch": spec.branch,
                    "worktree": str(spec.path),
                }
                for lane, spec in zip(candidate_lanes, result.lanes, strict=True)
            },
        }
        updated = dict(record)
        updated["bootstrap"] = bootstrap
        self._write_record(run_id, updated)
        return {"run_id": run_id, "status": "bootstrapped", **bootstrap}

    def execute(self, run_id: str) -> dict[str, object]:
        record = self._approved_record(run_id)
        if record.get("bootstrap") is None:
            raise FactoryStateError("factory run must be bootstrapped before execution")
        return self._execution().execute(run_id, str(record["provider_policy_path"]))

    def candidates(self, run_id: str) -> dict[str, object]:
        record = self._load_record(run_id)
        plan = AgentRunPlan.model_validate(record["engineering_blueprint"]["agent_run_plan"])
        state = self._agents.store.load(run_id)
        results = {
            task_id: AgentTaskResult.model_validate(value)
            for task_id, value in state["results"].items()
        }
        reviews = {decision.task_id: decision for decision in self._snapshot(run_id).reviews}
        values = []
        for task in plan.tasks:
            result = results.get(task.task_id)
            if result is None:
                continue
            values.append(
                {
                    "task_id": task.task_id,
                    "task_result": result,
                    "commit_sha": result.commit_sha,
                    "changed_paths": result.changed_paths,
                    "evidence": result.evidence,
                    "review": reviews.get(task.task_id),
                    "review_state": reviews.get(task.task_id).decision
                    if task.task_id in reviews
                    else "pending",
                }
            )
        return {"run_id": run_id, "candidates": tuple(values)}

    def review(
        self,
        run_id: str,
        task_id: str,
        decision: Mapping[str, object] | str | Path,
    ) -> CandidateReviewDecision:
        record = self._approved_record(run_id)
        bootstrap = self._require_bootstrap(record)
        raw = self._load_mapping(decision)
        if raw.get("run_id", run_id) != run_id or raw.get("task_id", task_id) != task_id:
            raise FactoryStateError("candidate review decision belongs to a different task or run")
        plan = AgentRunPlan.model_validate(record["engineering_blueprint"]["agent_run_plan"])
        try:
            task = next(item for item in plan.tasks if item.task_id == task_id)
            result = AgentTaskResult.model_validate(self._agents.store.load(run_id)["results"][task_id])
            repository = bootstrap["lanes"][task_id]["worktree"]
        except (KeyError, StopIteration) as error:
            raise FactoryStateError(f"candidate task is unavailable: {task_id}") from error

        inspected = self._review.review(
            decision_id=self._required_string(raw, "decision_id"),
            run_id=run_id,
            task=task,
            task_result=result,
            repository=repository,
            decided_by=str(raw.get("decided_by", "factory-reviewer")),
        )
        if raw.get("commit_sha", inspected.commit_sha) != inspected.commit_sha:
            raise FactoryStateError("candidate review decision names a different commit")
        if "changed_paths" in raw and tuple(raw["changed_paths"]) != inspected.changed_paths:
            raise FactoryStateError("candidate review decision names different changed paths")
        requested = raw.get("decision", inspected.decision)
        if requested == "accept" and inspected.decision != "accept":
            raise FactoryStateError("candidate inspection does not permit acceptance")
        if requested not in {"accept", "reject", "rework", "escalate"}:
            raise FactoryStateError("candidate review decision is invalid")
        recorded = CandidateReviewDecision.model_validate(
            {
                **inspected.model_dump(mode="json"),
                "decision": requested,
                "reason": raw.get("reason", inspected.reason),
            }
        )
        self._lifecycle.record_review(recorded)
        return recorded

    def integrate(self, run_id: str) -> ApplicationFactoryHandoff:
        record = self._approved_record(run_id)
        bootstrap = self._require_bootstrap(record)
        engineering = EngineeringBlueprint.model_validate(record["engineering_blueprint"])
        blueprint = self._blueprint_from_record(record)
        blueprint.load_modules()
        required = tuple(
            lane.lane_id
            for lane in engineering.lanes
            if not lane.integration_owned and lane.role != "assurance"
        )
        declared_commands = tuple(
            dict.fromkeys(
                command
                for lane in engineering.lanes
                if lane.integration_owned or lane.role == "assurance"
                for command in lane.verification_commands
            )
        )
        request = ApplicationIntegrationRequest(
            run_id=run_id,
            application_id=str(record["application_id"]),
            integration_branch=bootstrap["integration_branch"],
            required_task_ids=required,
            review_decisions=self._snapshot(run_id).reviews,
            verification_commands=declared_commands,
            allowed_verification_commands=declared_commands,
            expected_head=bootstrap["base_commit"],
            agent_handoff_ref=f"factory-runs/{run_id}/handoff",
        )
        handoff = self._integration.integrate(
            request,
            GitIntegrationRepository(bootstrap["integration_worktree"]),
        )
        self._lifecycle.record_handoff(handoff)
        return handoff

    def status(self, run_id: str) -> dict[str, object]:
        record = self._load_record(run_id)
        snapshot = self._snapshot(run_id)
        approval = self._approval_state(record, snapshot.approvals)
        agent_state: dict[str, object] | None = None
        if "engineering_blueprint" in record:
            try:
                agent_state = self._agents.status(run_id)
            except (FileNotFoundError, ValueError):
                agent_state = None
        usage: tuple[dict[str, object], ...] = ()
        events: tuple[dict[str, object], ...] = ()
        if record.get("bootstrap") is not None:
            execution = self._execution()
            usage_method = getattr(execution, "usage", None)
            events_method = getattr(execution, "events", None)
            if callable(usage_method):
                usage = tuple(usage_method(run_id))
            if callable(events_method):
                events = tuple(events_method(run_id))
        blockers = tuple(item.required_behavior for item in snapshot.unmet_requirements)
        if snapshot.handoff is not None:
            blockers += tuple(
                item.required_behavior for item in snapshot.handoff.unmet_requirements
            )
        return {
            "run_id": run_id,
            "factory_state": snapshot.handoff.status
            if snapshot.handoff is not None
            else "bootstrapped"
            if record.get("bootstrap") is not None
            else approval,
            "approval": approval,
            "reviews": snapshot.reviews,
            "usage": usage,
            "events": events,
            "blockers": blockers,
            "unmet_requirements": snapshot.unmet_requirements,
            "agent_run": agent_state,
            "verification": snapshot.handoff.verification_evidence
            if snapshot.handoff is not None
            else (),
            "integration_commit": snapshot.handoff.integration_commit
            if snapshot.handoff is not None
            else None,
            "handoff": snapshot.handoff,
        }

    def handoff(self, run_id: str) -> ApplicationFactoryHandoff:
        handoff = self._snapshot(run_id).handoff
        if handoff is None:
            raise FactoryStateError("factory run has no final handoff")
        return handoff

    def _selection_unmet(
        self,
        run_id: str,
        application_id: str,
        intent: ApplicationIntent,
        blueprint: ApplicationBlueprint,
    ) -> tuple[UnmetRequirement, ...]:
        unmet: list[UnmetRequirement] = []
        try:
            modules = blueprint.load_modules()
        except Exception as error:
            return (
                self._unmet(
                    run_id,
                    application_id,
                    "reviewed-kit",
                    f"No compatible reviewed framework kit exists: {error}",
                    "framework-kit",
                ),
            )
        for module in modules:
            for resource in module.resources:
                if not self._resources(resource):
                    unmet.append(
                        self._unmet(
                            run_id,
                            application_id,
                            f"resource-{module.module_id}-{resource.id}",
                            f"Resource {resource.id!r} for module {module.module_id!r} is unresolved.",
                            "platform",
                        )
                    )
        mapped = {
            str(file.document.get("metadata", {}).get("id"))
            for file in blueprint.static_files
            if file.document.get("kind") == "CapabilityDefinition"
        }
        for capability_id in sorted(set(intent.requested_capabilities) - mapped):
            unmet.append(
                self._unmet(
                    run_id,
                    application_id,
                    f"capability-{capability_id}",
                    f"Requested capability {capability_id!r} cannot be mapped by the reviewed blueprint.",
                    "application",
                )
            )
        return tuple(unmet)

    def _blocked_plan(
        self,
        run_id: str,
        application_id: str,
        repository: Path,
        intent: ApplicationIntent,
        blueprint: ApplicationBlueprint | None,
        unmet: tuple[UnmetRequirement, ...],
        *,
        profile: TechnologyProfile | None = None,
    ) -> dict[str, object]:
        for item in unmet:
            self._lifecycle.record_unmet_requirement(item)
        record: dict[str, object] = {
            "version": 1,
            "run_id": run_id,
            "application_id": application_id,
            "repository": str(repository),
            "intent": intent.model_dump(mode="json"),
            "planning_state": "blocked",
            "bootstrap": None,
        }
        if blueprint is not None:
            record.update(
                {
                    "application_blueprint_id": blueprint.blueprint_id,
                    "application_blueprint_version": blueprint.version,
                }
            )
        if profile is not None:
            record["technology_profile"] = profile.model_dump(mode="json")
        self._write_record(run_id, record, create=True)
        return {
            "run_id": run_id,
            "status": "blocked",
            "repository_created": False,
            "unmet_requirements": unmet,
        }

    def _materialize(
        self, repository: Path, application_id: str, blueprint: ApplicationBlueprint
    ) -> None:
        self.state_root.mkdir(parents=True, exist_ok=True)
        if repository.exists():
            existing = tuple(item.name for item in repository.iterdir() if item.name != ".git")
            if existing:
                raise FactoryStateError("application repository contains unexpected files")
        else:
            repository.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="factory-generation-", dir=self.state_root) as temporary:
            generated = self._generator.generate(
                GenerationRequest(
                    application_id=application_id,
                    display_name=blueprint.title,
                    blueprint=blueprint,
                    destination=Path(temporary),
                )
            )
            if repository.exists():
                for item in generated.root.iterdir():
                    target = repository / item.name
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
            else:
                shutil.move(str(generated.root), repository)

    def _write_guidance(
        self,
        repository: Path,
        profile: TechnologyProfile,
        engineering: EngineeringBlueprint,
    ) -> None:
        from servicefabric_agent_guidance import compose_guidance

        selections = {item.module_id: item for item in profile.module_selections}
        bundle = compose_guidance(
            {item.module_id: item.kit_reference for item in profile.module_selections}
        )
        for relative, content in bundle.files.items():
            target = repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        guidance_root = repository / ".servicefabric" / "factory" / "lanes"
        for lane in engineering.lanes:
            technology = tuple(
                selections[module_id]
                for module_id in lane.module_ids
                if module_id in selections
            )
            lines = [
                f"# Engineering Lane: {lane.lane_id}",
                "",
                f"Role: {lane.role}",
                f"Allowed paths: {', '.join(lane.allowed_paths)}",
                f"Expected outputs: {', '.join(lane.expected_outputs)}",
                "",
                "## Reviewed technology and techniques",
                "",
            ]
            if technology:
                for item in technology:
                    policies = ", ".join(item.technique_policy_ids) or "none"
                    lines.append(
                        f"- {item.module_id}: {item.kit_reference}; runtime {item.runtime_family}; "
                        f"technique policies {policies}."
                    )
            else:
                lines.append("- Application-level lane; use the approved engineering blueprint.")
            target = guidance_root / f"{lane.lane_id}.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            lane_guidance = "\n".join(lines).rstrip() + "\n"
            target.write_text(lane_guidance, encoding="utf-8")
            owned_agents = repository / PurePosixPath(lane.allowed_paths[0]) / "AGENTS.md"
            owned_agents.parent.mkdir(parents=True, exist_ok=True)
            owned_agents.write_text(lane_guidance, encoding="utf-8")

    @staticmethod
    def _initialize_base(repository: Path, run_id: str) -> str:
        if not (repository / ".git").exists():
            ApplicationFactoryService._run_git(repository, "init", "-b", "main")
        ApplicationFactoryService._run_git(repository, "rev-parse", "--show-toplevel")
        if ApplicationFactoryService._run_git(repository, "status", "--porcelain", check=True).strip():
            ApplicationFactoryService._run_git(repository, "add", "--all")
            ApplicationFactoryService._run_git(
                repository,
                "-c",
                "user.name=ServiceFabric Factory",
                "-c",
                "user.email=factory@servicefabric.invalid",
                "commit",
                "-m",
                f"chore(factory): preserve approved base for {run_id}",
            )
        return ApplicationFactoryService._run_git(repository, "rev-parse", "HEAD").strip()

    @staticmethod
    def _run_git(repository: Path, *arguments: str, check: bool = True) -> str:
        completed = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=False,
            capture_output=True,
            text=True,
        )
        if check and completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown Git error"
            raise FactoryStateError(f"git {' '.join(arguments)} failed: {detail}")
        return completed.stdout

    def _approved_record(self, run_id: str) -> dict[str, Any]:
        record = self._load_record(run_id)
        if self._approval_state(record, self._snapshot(run_id).approvals) != "approved":
            raise FactoryStateError("exact technology profile and blueprint require explicit approval")
        return record

    @staticmethod
    def _approval_state(
        record: Mapping[str, object], approvals: tuple[FactoryApprovalDecision, ...]
    ) -> str:
        relevant = tuple(
            item for item in approvals if item.subject_ref == record.get("approval_subject_ref")
        )
        if not relevant:
            return str(record.get("planning_state", "pending_approval"))
        return {"approve": "approved", "reject": "rejected", "revise": "revision_requested"}[
            relevant[0].decision
        ]

    def _execution(self) -> _ProviderExecution:
        if self._provider_execution is None:
            self._provider_execution = ProviderExecutionService(
                self._agents, default_provider_registry()
            )
        return self._provider_execution

    def _snapshot(self, run_id: str):
        try:
            return self._lifecycle.load(run_id)
        except FileNotFoundError:
            from servicefabric_application_factory_state import FactoryLifecycleSnapshot

            return FactoryLifecycleSnapshot(run_id, (), (), (), None)

    def _resolve_blueprint(self, blueprint_id: str) -> ApplicationBlueprint:
        matches = tuple(item for item in self._catalog.list() if item.blueprint_id == blueprint_id)
        if len(matches) != 1:
            raise FactoryStateError(
                f"reviewed blueprint {blueprint_id!r} must resolve to exactly one version"
            )
        return self._catalog.resolve(matches[0].blueprint_id, matches[0].version)

    def _blueprint_from_record(self, record: Mapping[str, object]) -> ApplicationBlueprint:
        return self._catalog.resolve(
            str(record["application_blueprint_id"]),
            str(record["application_blueprint_version"]),
        )

    @staticmethod
    def _required_lifecycle(primitive: str) -> tuple[str, ...]:
        normalized = primitive.rsplit(".", 1)[-1].lower()
        return ("development", "build") if normalized == "library" else (
            "development",
            "build",
            "runtime",
        )

    @staticmethod
    def _load_intent(value: ApplicationIntent | str | Path) -> ApplicationIntent:
        if isinstance(value, ApplicationIntent):
            return value
        return ApplicationIntent.model_validate(
            json.loads(Path(value).read_text(encoding="utf-8"))
        )

    @staticmethod
    def _load_policy(value: ProviderPolicy | str | Path) -> ProviderPolicy:
        return value if isinstance(value, ProviderPolicy) else load_provider_policy(value)

    @staticmethod
    def _load_contract(value: object, contract: Any):
        if isinstance(value, contract):
            return value
        return contract.model_validate(
            json.loads(Path(value).read_text(encoding="utf-8"))
        )

    @staticmethod
    def _load_mapping(value: Mapping[str, object] | str | Path) -> dict[str, object]:
        loaded: object = value
        if not isinstance(value, Mapping):
            loaded = json.loads(Path(value).read_text(encoding="utf-8"))
        if not isinstance(loaded, Mapping):
            raise FactoryStateError("decision file must contain a JSON object")
        return dict(loaded)

    @staticmethod
    def _required_string(value: Mapping[str, object], key: str) -> str:
        item = value.get(key)
        if not isinstance(item, str) or not item:
            raise FactoryStateError(f"decision requires a non-empty {key}")
        return item

    @staticmethod
    def _require_bootstrap(record: Mapping[str, object]) -> dict[str, Any]:
        value = record.get("bootstrap")
        if not isinstance(value, dict):
            raise FactoryStateError("factory run must be bootstrapped")
        return value

    @staticmethod
    def _unmet(
        run_id: str,
        application_id: str,
        suffix: str,
        behavior: str,
        scope: str,
    ) -> UnmetRequirement:
        safe_suffix = "-".join(
            part for part in shlex.split(suffix.replace("/", "-")) if part
        ).lower()
        return UnmetRequirement(
            requirement_id=f"unmet-{safe_suffix}",
            application_id=application_id,
            run_id=run_id,
            required_behavior=behavior or "Reviewed factory requirement could not be met.",
            proposed_scope=scope,
            urgency="high",
        )

    def _record_path(self, run_id: str) -> Path:
        return self.state_root / "plans" / f"{run_id}.json"

    def _artifact_path(self, run_id: str, name: str) -> Path:
        return self.state_root / "artifacts" / run_id / name

    def _load_record(self, run_id: str) -> dict[str, Any]:
        value = json.loads(self._record_path(run_id).read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("run_id") != run_id:
            raise FactoryStateError(f"invalid factory planning record for {run_id!r}")
        return value

    def _write_record(
        self, run_id: str, value: Mapping[str, object], *, create: bool = False
    ) -> None:
        target = self._record_path(run_id)
        if create and target.exists():
            existing = self._load_record(run_id)
            if existing != value:
                raise FactoryStateError(f"factory run {run_id!r} already has a different plan")
            return
        self._atomic_json(target, value)

    @staticmethod
    def _atomic_json(target: Path, value: object) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        try:
            temporary.write_text(
                json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _digest(value: object) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "ApplicationFactoryService",
    "FactoryStateError",
    "GitIntegrationRepository",
]
