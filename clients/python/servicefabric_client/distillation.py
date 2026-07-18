"""Public Wave-10 composition over accepted distillation package APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
import fcntl
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Any, Mapping, Protocol

from servicefabric_agentic_contracts import AgentTaskResult
from servicefabric_application_evidence import (
    ApplicationEvidenceCollector,
    EvidenceCollectionRequest,
    ManifestEvidence,
)
from servicefabric_application_factory_contracts import EngineeringBlueprint, TechnologyProfile
from servicefabric_capability_distillation import (
    CapabilityDistillationRequest,
    distill_capability_candidates,
)
from servicefabric_capability_model import CapabilityDefinition
from servicefabric_capability_registry import CapabilityRegistry
from servicefabric_distillation_contracts import (
    ApplicationEvidenceBundle,
    BlueprintEvolutionProposal,
    CapabilityCandidate,
    DistillationDecision,
    DistillationReport,
    EngineeringPatternCandidate,
    SystemChangeProposal,
    TechniquePolicyCandidate,
    TechniquePolicyDefinition,
)
from servicefabric_engineering_distillation import EngineeringPatternCatalog
from servicefabric_evolution_proposals import propose_blueprint_evolutions, propose_system_changes
from servicefabric_operation_model import OperationDefinition
from servicefabric_technique_policies import (
    TechniquePolicyCatalog,
    candidate_from_profile_and_evidence,
)


class DistillationError(ValueError):
    """Raised when composition inputs exceed the reviewed boundary."""


class FactoryEvidenceSource(Protocol):
    def distillation_inputs(self, run_id: str) -> dict[str, object]: ...


@dataclass(frozen=True)
class ManifestSource:
    """One exact, explicitly named manifest or declared artifact."""

    ref: str
    path: str
    source_paths: tuple[str, ...] = ()
    operation_refs: tuple[str, ...] = ()
    capability_refs: tuple[str, ...] = ()
    documentation_refs: tuple[str, ...] = ()
    verification_evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class DistillationInputs:
    run_id: str
    manifests: tuple[ManifestSource, ...]
    declared_operations: tuple[OperationDefinition, ...]
    declared_capabilities: tuple[CapabilityDefinition, ...]
    technique_policy_definitions: tuple[TechniquePolicyDefinition, ...] = ()
    blueprint_categories: Mapping[str, str] = field(default_factory=dict)
    system_scopes: Mapping[str, str] = field(default_factory=dict)
    engineering_pattern_version: str | None = None


@dataclass(frozen=True)
class CollectedEvidence:
    bundle: ApplicationEvidenceBundle
    factory: Mapping[str, object]


@dataclass(frozen=True)
class DistillationAnalysis:
    collected: CollectedEvidence
    technique_evidence: ApplicationEvidenceBundle
    capability_candidates: tuple[CapabilityCandidate, ...]
    technique_policy_candidates: tuple[TechniquePolicyCandidate, ...]
    engineering_pattern_candidates: tuple[EngineeringPatternCandidate, ...]
    blueprint_proposals: tuple[BlueprintEvolutionProposal, ...]
    system_proposals: tuple[SystemChangeProposal, ...]
    known_limitations: tuple[str, ...] = ()

    @property
    def candidates(self) -> tuple[object, ...]:
        groups = (
            self.capability_candidates,
            self.technique_policy_candidates,
            self.engineering_pattern_candidates,
            self.blueprint_proposals,
            self.system_proposals,
        )
        return tuple(item for group in groups for item in sorted(group, key=_identity))


@dataclass(frozen=True)
class DistillationResult:
    report: DistillationReport
    evidence_summary: Mapping[str, object]
    candidates: tuple[object, ...]
    decisions: tuple[DistillationDecision, ...]
    published_references: tuple[str, ...]
    blueprint_proposals: tuple[BlueprintEvolutionProposal, ...]
    system_proposals: tuple[SystemChangeProposal, ...]
    run_metrics: Mapping[str, int | float]
    known_limitations: tuple[str, ...]


class FileDistillationDecisionStore:
    """Immutable decision records only; this is not a factory or agent run store."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def record(self, decision: DistillationDecision) -> DistillationDecision:
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = self.root / f"{decision.decision_id}.json"
        lock = self.root / ".decisions.lock"
        with lock.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                serialized = decision.model_dump(mode="json", by_alias=True)
                for path in sorted(self.root.glob("*.json")):
                    existing_for_candidate = DistillationDecision.model_validate(
                        json.loads(path.read_text(encoding="utf-8"))
                    )
                    if (
                        existing_for_candidate.candidate_ref == decision.candidate_ref
                        and existing_for_candidate != decision
                    ):
                        raise DistillationError(
                            f"candidate {decision.candidate_ref!r} already has an immutable decision"
                        )
                if target.exists():
                    existing = DistillationDecision.model_validate(
                        json.loads(target.read_text(encoding="utf-8"))
                    )
                    if existing != decision:
                        raise DistillationError(
                            f"decision {decision.decision_id!r} is already immutable"
                        )
                    return existing
                descriptor, temporary = tempfile.mkstemp(
                    prefix=".distillation-decision-", suffix=".tmp", dir=self.root
                )
                try:
                    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                        json.dump(serialized, output, sort_keys=True, separators=(",", ":"))
                        output.flush()
                        os.fsync(output.fileno())
                    os.replace(temporary, target)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
                return decision
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def list(self) -> tuple[DistillationDecision, ...]:
        if not self.root.exists():
            return ()
        return tuple(
            DistillationDecision.model_validate(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(self.root.glob("*.json"))
        )


class DistillationService:
    """Collect, analyze, decide, publish, and report through canonical authorities."""

    def __init__(
        self,
        factory: FactoryEvidenceSource,
        capability_registry: CapabilityRegistry,
        technique_catalog: TechniquePolicyCatalog,
        engineering_catalog: EngineeringPatternCatalog,
        decisions: FileDistillationDecisionStore,
    ) -> None:
        self._factory = factory
        self._capabilities = capability_registry
        self._techniques = technique_catalog
        self._engineering = engineering_catalog
        self._decisions = decisions

    @classmethod
    def for_current_environment(cls, workspace: object | None = None) -> "DistillationService":
        from servicefabric_workspace import resolve_workspace

        from .application_factory import ApplicationFactoryService

        context = workspace or resolve_workspace()
        layout = context.layout
        configured = os.environ.get("SERVICEFABRIC_HOME")
        factory_root = (
            Path(configured).expanduser() / "factory-runs" / "wave-09"
            if configured
            else Path.cwd() / ".sf-agent-runtime" / "wave-09"
        )
        state_root = layout.state / "distillation"
        return cls(
            ApplicationFactoryService(factory_root),
            CapabilityRegistry(layout.registry / "capabilities"),
            TechniquePolicyCatalog(state_root / "technique-policies"),
            EngineeringPatternCatalog(state_root / "engineering-patterns"),
            FileDistillationDecisionStore(state_root / "decisions"),
        )

    def collect(self, inputs: DistillationInputs) -> CollectedEvidence:
        factory = self._factory.distillation_inputs(inputs.run_id)
        root = Path(str(factory["repository_root"])).resolve()
        manifests = tuple(self._load_source(root, source) for source in inputs.manifests)
        if not manifests:
            raise DistillationError("at least one explicit application manifest is required")
        handoff = factory["agent_handoff"]
        factory_handoff = factory["factory_handoff"]
        bundle = ApplicationEvidenceCollector().collect(
            EvidenceCollectionRequest(
                bundle_id=f"evidence-{inputs.run_id}",
                repository_head=str(factory["repository_head"]),
                application_blueprint_id=str(factory["application_blueprint_id"]),
                technology_profile_id=factory["technology_profile"].profile_id,
                factory_run_id=inputs.run_id,
                manifests=manifests,
                agent_run_plan=factory["agent_run_plan"],
                agent_handoff=handoff,
                factory_handoff=factory_handoff,
            )
        )
        requirements = tuple(factory["unmet_requirements"]) + tuple(factory_handoff.unmet_requirements)
        requirement_refs = tuple(sorted({item.requirement_id for item in requirements}))
        bundle = bundle.model_copy(update={"unmet_requirement_refs": requirement_refs})
        return CollectedEvidence(bundle, factory)

    def analyze(self, inputs: DistillationInputs) -> DistillationAnalysis:
        collected = self.collect(inputs)
        bundle = collected.bundle
        capability_candidates = distill_capability_candidates(
            CapabilityDistillationRequest(
                bundle, inputs.declared_operations, inputs.declared_capabilities,
                tuple(sorted(bundle.verification_evidence_refs)),
            )
        )
        profile: TechnologyProfile = collected.factory["technology_profile"]  # type: ignore[assignment]
        technique_evidence = bundle.model_copy(update={"unmet_requirement_refs": ()})
        technique_candidates = tuple(
            sorted(
                (
                    candidate_from_profile_and_evidence(definition, profile, technique_evidence)
                    for definition in inputs.technique_policy_definitions
                ),
                key=_identity,
            )
        )
        engineering: EngineeringBlueprint = collected.factory["engineering_blueprint"]  # type: ignore[assignment]
        pattern = self._engineering_candidate(engineering, bundle)
        blueprint_version = str(collected.factory["application_blueprint_version"])
        blueprint_proposals = propose_blueprint_evolutions(
            bundle,
            blueprint_version=blueprint_version,
            category_by_requirement=inputs.blueprint_categories,
        )
        allowed_scopes = {
            requirement: scope
            for requirement, scope in inputs.system_scopes.items()
            if scope in {"library", "framework-kit", "primitive", "platform"}
        }
        scoped_bundle = bundle.model_copy(
            update={"unmet_requirement_refs": tuple(sorted(allowed_scopes))}
        )
        system_proposals = propose_system_changes(
            (scoped_bundle,), scope_by_requirement=allowed_scopes, minimum_recurrence=1
        ) if allowed_scopes else ()
        missing_scopes = tuple(sorted(set(bundle.unmet_requirement_refs) - set(allowed_scopes)))
        limitations = (
            "Blueprint and system proposals are records only and are never applied.",
            "Analysis uses explicit manifests and declared artifacts only; repository discovery is disabled.",
            "Technique reuse is evaluated from successful verification independently of unrelated unmet requirements.",
            *(f"No explicit system scope was supplied for {item}." for item in missing_scopes),
        )
        return DistillationAnalysis(
            collected,
            technique_evidence,
            capability_candidates,
            technique_candidates,
            (pattern,),
            blueprint_proposals,
            system_proposals,
            tuple(limitations),
        )

    def candidates(self, inputs: DistillationInputs) -> tuple[object, ...]:
        return self.analyze(inputs).candidates

    def decide(self, decision: DistillationDecision) -> DistillationDecision:
        return self._decisions.record(decision)

    def publish(self, analysis: DistillationAnalysis, *, engineering_version: str) -> DistillationResult:
        candidates = analysis.candidates
        candidate_ids = {_identity(item) for item in candidates}
        decisions = tuple(
            item for item in self._decisions.list() if item.candidate_ref in candidate_ids
        )
        by_candidate = {item.candidate_ref: item for item in decisions}
        published: list[str] = []
        for candidate in analysis.capability_candidates:
            decision = by_candidate.get(candidate.candidate_id)
            if decision is not None and decision.decision == "approve":
                record = self._capabilities.register(
                    candidate.proposed_definition, candidate.application_id
                ).record
                published.append(f"capability:{record.definition.metadata.id}")
        profile: TechnologyProfile = analysis.collected.factory["technology_profile"]  # type: ignore[assignment]
        for candidate in analysis.technique_policy_candidates:
            decision = by_candidate.get(candidate.candidate_id)
            if decision is not None and decision.decision == "approve":
                record = self._techniques.publish(
                    candidate, decision, profile, analysis.technique_evidence
                )
                published.append(
                    f"technique-policy:{record.definition.policy_id}@{record.definition.version}"
                )
        for candidate in analysis.engineering_pattern_candidates:
            decision = by_candidate.get(candidate.candidate_id)
            if decision is not None and decision.decision == "approve":
                record = self._engineering.publish(candidate, decision, engineering_version).publication
                published.append(f"engineering-pattern:{record.pattern_id}@{record.version}")
        return self._result(analysis, decisions, tuple(sorted(published)))

    def report(self, inputs: DistillationInputs) -> DistillationResult:
        analysis = self.analyze(inputs)
        version = inputs.engineering_pattern_version or str(
            analysis.collected.factory["application_blueprint_version"]
        )
        return self.publish(analysis, engineering_version=version)

    def _load_source(self, root: Path, source: ManifestSource) -> ManifestEvidence:
        relative = PurePosixPath(source.path)
        if relative.is_absolute() or ".." in relative.parts or "\\" in source.path:
            raise DistillationError(f"unsafe declared artifact path: {source.path!r}")
        target = (root / relative.as_posix()).resolve()
        if not target.is_relative_to(root) or not target.is_file() or target.is_symlink():
            raise DistillationError(f"declared artifact is not an exact regular file: {source.path!r}")
        return ManifestEvidence(
            ref=source.ref,
            content=target.read_bytes(),
            source_paths=source.source_paths,
            operation_refs=source.operation_refs,
            capability_refs=source.capability_refs,
            documentation_refs=source.documentation_refs,
            verification_evidence_refs=source.verification_evidence_refs,
        )

    @staticmethod
    def _engineering_candidate(
        engineering: EngineeringBlueprint, bundle: ApplicationEvidenceBundle
    ) -> EngineeringPatternCandidate:
        lanes = tuple(lane.lane_id for lane in engineering.lanes)
        verification = tuple(
            dict.fromkeys(command for lane in engineering.lanes for command in lane.verification_commands)
        )
        usage_ref = next(
            (item for item in bundle.verification_evidence_refs if item.startswith("provider-usage:")),
            None,
        )
        return EngineeringPatternCandidate(
            candidate_id=f"engineering-pattern.{engineering.blueprint_id}",
            source_blueprint_ref=f"engineering:{engineering.blueprint_id}",
            lane_topology=lanes,
            provider_role_mapping={lane.lane_id: lane.provider_role for lane in engineering.lanes},
            path_ownership={lane.lane_id: lane.allowed_paths for lane in engineering.lanes},
            dependency_order=lanes,
            verification_profile=verification,
            observed_usage_ref=usage_ref,
            evidence_refs=(f"bundle:{bundle.bundle_id}", *bundle.verification_evidence_refs),
            status="proposed",
        )

    @staticmethod
    def _result(
        analysis: DistillationAnalysis,
        decisions: tuple[DistillationDecision, ...],
        published: tuple[str, ...],
    ) -> DistillationResult:
        bundle = analysis.collected.bundle
        candidates = analysis.candidates
        results: tuple[AgentTaskResult, ...] = analysis.collected.factory["agent_task_results"]  # type: ignore[assignment]
        metrics: dict[str, int | float] = {
            "manifest_count": len(bundle.exact_manifest_refs),
            "changed_path_count": len(bundle.changed_path_refs),
            "candidate_count": len(candidates),
            "decision_count": len(decisions),
            "published_count": len(published),
            "task_count": len(results),
            "successful_task_count": sum(item.status == "success" for item in results),
            "verification_evidence_count": len(bundle.verification_evidence_refs),
        }
        proposal_refs = tuple(
            _identity(item) for item in (*analysis.blueprint_proposals, *analysis.system_proposals)
        )
        report = DistillationReport(
            distillation_id=f"distillation-{analysis.collected.factory['run_id']}",
            application_id=bundle.application_id,
            evidence_bundle_ref=f"bundle:{bundle.bundle_id}",
            candidate_refs=tuple(_identity(item) for item in candidates),
            decision_refs=tuple(f"decision:{item.decision_id}" for item in decisions),
            published_refs=published,
            proposal_refs=proposal_refs,
            deterministic_metrics=metrics,
        )
        summary = {
            "bundle_id": bundle.bundle_id,
            "repository_head": bundle.repository_head,
            "manifest_refs": bundle.exact_manifest_refs,
            "changed_path_refs": bundle.changed_path_refs,
            "verification_evidence_refs": bundle.verification_evidence_refs,
            "unmet_requirement_refs": bundle.unmet_requirement_refs,
        }
        return DistillationResult(
            report, summary, candidates, decisions, published,
            analysis.blueprint_proposals, analysis.system_proposals,
            metrics, analysis.known_limitations,
        )


def foundation_diagnostics(workspace: object) -> dict[str, object]:
    """Run local, free, secret-safe foundation checks without provider execution."""

    from servicefabric_blueprints import create_default_blueprint_catalog
    from servicefabric_framework_kits import get_default_catalog

    from .agent_providers import default_provider_registry
    from .capabilities import registry_for_workspace

    layout = workspace.layout
    checks: list[dict[str, object]] = []
    package_names = (
        "servicefabric_application_evidence",
        "servicefabric_capability_distillation",
        "servicefabric_technique_policies",
        "servicefabric_engineering_distillation",
        "servicefabric_evolution_proposals",
        "servicefabric_release_readiness",
    )
    for name in package_names:
        try:
            importlib.import_module(name)
            checks.append({"name": f"package:{name}", "status": "pass"})
        except Exception as error:
            checks.append({"name": f"package:{name}", "status": "fail", "detail": str(error)})

    from servicefabric_workspace import WorkspaceService

    validation = WorkspaceService(workspace).validate()
    checks.append({"name": "workspace", "status": "pass" if validation.valid else "fail"})
    try:
        blueprints = create_default_blueprint_catalog().list()
        for blueprint in blueprints:
            blueprint.load_modules(get_default_catalog())
        checks.append({"name": "blueprint-and-kit-catalogs", "status": "pass", "count": len(blueprints)})
    except Exception as error:
        checks.append({"name": "blueprint-and-kit-catalogs", "status": "fail", "detail": str(error)})

    providers = default_provider_registry()
    registrations = providers.list()
    checks.append({"name": "provider-adapters", "status": "pass", "providers": registrations})
    try:
        registry_for_workspace(layout).list()
        TechniquePolicyCatalog(layout.state / "distillation" / "technique-policies").list()
        EngineeringPatternCatalog(layout.state / "distillation" / "engineering-patterns").list()
        checks.append({"name": "registries-and-catalogs", "status": "pass"})
    except Exception as error:
        checks.append({"name": "registries-and-catalogs", "status": "fail", "detail": str(error)})

    state_paths = (layout.registry, layout.state / "distillation", layout.locks)
    writable = True
    for path in state_paths:
        try:
            path.mkdir(parents=True, exist_ok=True)
            writable = writable and os.access(path, os.W_OK)
        except OSError:
            writable = False
    checks.append({"name": "writable-state-paths", "status": "pass" if writable else "fail"})

    executables = tuple(
        {
            "provider_id": adapter.provider_id,
            "executable": adapter.probe().get("executable"),
            "available": shutil.which(str(adapter.probe().get("executable"))) is not None,
        }
        for adapter in providers.adapters()
    )
    checks.append({"name": "declared-executables", "status": "pass", "executables": executables})
    return {"ok": all(item["status"] == "pass" for item in checks), "checks": tuple(checks)}


def _identity(value: object) -> str:
    for name in ("candidate_id", "proposal_id"):
        item = getattr(value, name, None)
        if isinstance(item, str):
            return item
    raise TypeError(f"unsupported distillation candidate: {type(value).__name__}")


__all__ = [
    "CollectedEvidence",
    "DistillationAnalysis",
    "DistillationError",
    "DistillationInputs",
    "DistillationResult",
    "DistillationService",
    "FileDistillationDecisionStore",
    "ManifestSource",
    "foundation_diagnostics",
]
