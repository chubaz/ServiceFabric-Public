"""Collect Wave-9 references without discovering repository or runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Mapping

from servicefabric_agentic_contracts import AgentHandoff, AgentRunPlan
from servicefabric_application_factory_contracts import ApplicationFactoryHandoff
from servicefabric_contracts.common import OperationReference
from servicefabric_distillation_contracts import ApplicationEvidenceBundle


class EvidenceCollectionError(ValueError):
    """Raised when supplied evidence exceeds the declared manifest boundary."""


def _reference(value: str, *, label: str) -> str:
    if not value or not value.strip():
        raise EvidenceCollectionError(f"{label} must be a non-empty reference")
    return value


def _path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or "\\" in value
        or ".." in candidate.parts
        or candidate == PurePosixPath(".")
    ):
        raise EvidenceCollectionError(f"unsafe path reference: {value!r}")
    return candidate.as_posix()


def _is_declared_path(path: str, declared_paths: tuple[str, ...]) -> bool:
    parts = PurePosixPath(path).parts
    return any(parts[: len(PurePosixPath(declared).parts)] == PurePosixPath(declared).parts for declared in declared_paths)


@dataclass(frozen=True)
class ManifestEvidence:
    """One explicit application manifest and the references it declares.

    ``content`` is supplied by the caller.  The collector deliberately never
    resolves a ref to a path or reads it from disk.
    """

    ref: str
    content: str | bytes
    source_paths: tuple[str, ...] = field(default_factory=tuple)
    operation_refs: tuple[OperationReference, ...] = field(default_factory=tuple)
    capability_refs: tuple[str, ...] = field(default_factory=tuple)
    documentation_refs: tuple[str, ...] = field(default_factory=tuple)
    verification_evidence_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvidenceCollectionRequest:
    """All explicit, already-authoritative inputs for one evidence bundle."""

    bundle_id: str
    repository_head: str
    application_blueprint_id: str
    manifests: tuple[ManifestEvidence, ...]
    agent_run_plan: AgentRunPlan
    agent_handoff: AgentHandoff
    factory_handoff: ApplicationFactoryHandoff | None = None
    technology_profile_id: str | None = None
    factory_run_id: str | None = None


class ApplicationEvidenceCollector:
    """Build immutable bundles from declared references and reported results only."""

    def collect(self, request: EvidenceCollectionRequest) -> ApplicationEvidenceBundle:
        manifests = self._validate_request(request)
        task_ids = {task.task_id for task in request.agent_run_plan.tasks}
        results = {result.task_id: result for result in request.agent_handoff.task_results}
        unknown_results = set(results) - task_ids
        if unknown_results:
            raise EvidenceCollectionError(
                "handoff contains task results absent from plan: " + ", ".join(sorted(unknown_results))
            )

        declared_paths = tuple(
            sorted({path for manifest in manifests for path in manifest.source_paths})
        )
        changed_paths: set[str] = set()
        verification_refs: set[str] = set()
        for task_id, result in results.items():
            task = next(task for task in request.agent_run_plan.tasks if task.task_id == task_id)
            for changed_path in result.changed_paths:
                normalized = _path(changed_path)
                if not _is_declared_path(normalized, declared_paths) or not _is_declared_path(
                    normalized, tuple(_path(path) for path in task.allowed_paths)
                ):
                    raise EvidenceCollectionError(
                        f"task {task_id!r} reported undeclared changed path {changed_path!r}"
                    )
                changed_paths.add(normalized)
            verification_refs.update(
                evidence.artifact_ref
                for evidence in result.evidence
                if evidence.artifact_ref is not None
            )

        operation_refs = tuple(sorted({item for manifest in manifests for item in manifest.operation_refs}))
        capability_refs = tuple(sorted({item for manifest in manifests for item in manifest.capability_refs}))
        documentation_refs = tuple(sorted({item for manifest in manifests for item in manifest.documentation_refs}))
        verification_refs.update(
            reference for manifest in manifests for reference in manifest.verification_evidence_refs
        )

        review_refs: set[str] = set()
        unmet_refs: set[str] = set()
        if request.factory_handoff is not None:
            self._validate_factory_handoff(request)
            review_refs.update(request.factory_handoff.review_decision_refs)
            verification_refs.update(request.factory_handoff.verification_evidence)
            unmet_refs.update(
                reference
                for requirement in request.factory_handoff.unmet_requirements
                for reference in requirement.evidence_refs
            )

        content_digests = {
            manifest.ref: "sha256:" + sha256(
                manifest.content.encode("utf-8") if isinstance(manifest.content, str) else manifest.content
            ).hexdigest()
            for manifest in manifests
        }
        return ApplicationEvidenceBundle(
            bundle_id=request.bundle_id,
            application_id=request.agent_run_plan.intent.application_id
            or request.application_blueprint_id,
            repository_head=request.repository_head,
            application_blueprint_id=request.application_blueprint_id,
            technology_profile_id=request.technology_profile_id,
            factory_run_id=request.factory_run_id,
            exact_manifest_refs=tuple(manifest.ref for manifest in manifests),
            operation_refs=operation_refs,
            capability_refs=capability_refs,
            changed_path_refs=tuple(sorted(changed_paths)),
            verification_evidence_refs=tuple(sorted(verification_refs)),
            review_decision_refs=tuple(sorted(review_refs)),
            unmet_requirement_refs=tuple(sorted(unmet_refs)),
            documentation_refs=documentation_refs,
            content_digests=content_digests,
        )

    @staticmethod
    def _validate_request(request: EvidenceCollectionRequest) -> tuple[ManifestEvidence, ...]:
        if request.agent_handoff.run_id != request.agent_run_plan.run_id:
            raise EvidenceCollectionError("agent handoff must belong to the supplied run plan")
        if request.factory_run_id is not None and request.factory_run_id != request.agent_run_plan.run_id:
            raise EvidenceCollectionError("factory run ID must match the supplied run plan")
        if not request.manifests:
            raise EvidenceCollectionError("at least one explicit manifest is required")
        manifests = tuple(sorted(request.manifests, key=lambda item: item.ref))
        refs = [item.ref for item in manifests]
        if len(set(refs)) != len(refs):
            raise EvidenceCollectionError("manifest references must be unique")
        for manifest in manifests:
            _reference(manifest.ref, label="manifest ref")
            for path in manifest.source_paths:
                _path(path)
            for value in (
                *manifest.capability_refs,
                *manifest.documentation_refs,
                *manifest.verification_evidence_refs,
            ):
                _reference(value, label="manifest-declared reference")
        return manifests

    @staticmethod
    def _validate_factory_handoff(request: EvidenceCollectionRequest) -> None:
        assert request.factory_handoff is not None
        if request.factory_handoff.run_id != request.agent_run_plan.run_id:
            raise EvidenceCollectionError("factory handoff must belong to the supplied run plan")
        if request.factory_handoff.application_id != (
            request.agent_run_plan.intent.application_id or request.application_blueprint_id
        ):
            raise EvidenceCollectionError("factory handoff application does not match evidence request")
