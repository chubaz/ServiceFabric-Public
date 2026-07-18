"""Contracts only; collection, review, and publication belong to owning lanes."""
from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field
from servicefabric_capability_model import CapabilityDefinition
from servicefabric_contracts.common import (
    Digest,
    Identifier,
    ImmutableContractModel,
    OperationReference,
)


class _DistillationContract(ImmutableContractModel):
    model_config = ImmutableContractModel.model_config | ConfigDict(populate_by_name=True)


class ApplicationEvidenceBundle(_DistillationContract):
    bundle_id: Identifier
    application_id: Identifier
    repository_head: str = Field(pattern=r"^[0-9a-f]{7,64}$")
    application_blueprint_id: Identifier
    technology_profile_id: Identifier | None = None
    factory_run_id: Identifier | None = None
    exact_manifest_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    operation_refs: tuple[OperationReference, ...] = Field(default_factory=tuple, max_length=256)
    capability_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    changed_path_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=512)
    verification_evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    review_decision_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    unmet_requirement_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    documentation_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    content_digests: dict[str, Digest] = Field(default_factory=dict, max_length=1024)


class CapabilityCandidate(_DistillationContract):
    candidate_id: Identifier
    application_id: Identifier
    operation_ref: OperationReference
    proposed_definition: CapabilityDefinition
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    rationale: str = Field(min_length=1, max_length=4000)
    confidence: float = Field(ge=0, le=1)
    status: str = Field(min_length=1, max_length=64)


class TechniquePolicyDefinition(_DistillationContract):
    policy_id: Identifier
    version: str = Field(min_length=1, max_length=128)
    applicable_primitives: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    applicable_kit_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    approved_libraries: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    approved_techniques: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    prohibited_patterns: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    required_guidance: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    verification_commands: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)


class TechniquePolicyCandidate(_DistillationContract):
    candidate_id: Identifier
    proposed_definition: TechniquePolicyDefinition
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    rationale: str = Field(min_length=1, max_length=4000)
    confidence: float = Field(ge=0, le=1)
    status: str = Field(min_length=1, max_length=64)


class EngineeringPatternCandidate(_DistillationContract):
    candidate_id: Identifier
    source_blueprint_ref: str = Field(min_length=1, max_length=512)
    lane_topology: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    provider_role_mapping: dict[str, str] = Field(default_factory=dict, max_length=256)
    path_ownership: dict[str, tuple[str, ...]] = Field(default_factory=dict, max_length=256)
    dependency_order: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    verification_profile: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    observed_usage_ref: str | None = Field(default=None, min_length=1, max_length=512)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    status: str = Field(min_length=1, max_length=64)


class BlueprintEvolutionProposal(_DistillationContract):
    proposal_id: Identifier
    blueprint_id: Identifier
    blueprint_version: str = Field(min_length=1, max_length=128)
    category: Literal["module", "kit", "resource", "lifecycle", "verification", "guidance"]
    required_behavior: str = Field(min_length=1, max_length=4000)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    proposed_change: str = Field(min_length=1, max_length=8000)
    status: str = Field(min_length=1, max_length=64)


class SystemChangeProposal(_DistillationContract):
    proposal_id: Identifier
    source_requirement_ref: str = Field(min_length=1, max_length=512)
    proposed_scope: Literal["library", "framework-kit", "primitive", "platform"]
    required_behavior: str = Field(min_length=1, max_length=4000)
    recurrence_count: int = Field(ge=1)
    affected_applications: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=256)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    urgency: str = Field(min_length=1, max_length=64)
    status: str = Field(min_length=1, max_length=64)


class DistillationDecision(_DistillationContract):
    decision_id: Identifier
    candidate_ref: str = Field(min_length=1, max_length=512)
    decision: Literal["approve", "reject", "revise"]
    reason: str = Field(min_length=1, max_length=4000)
    decided_by: str = Field(min_length=1, max_length=256)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=256)


class DistillationReport(_DistillationContract):
    distillation_id: Identifier
    application_id: Identifier
    evidence_bundle_ref: str = Field(min_length=1, max_length=512)
    candidate_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=512)
    decision_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=512)
    published_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=512)
    proposal_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=512)
    deterministic_metrics: dict[str, int | float] = Field(default_factory=dict, max_length=256)
