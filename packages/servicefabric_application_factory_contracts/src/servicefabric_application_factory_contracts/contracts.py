"""Contracts only; factory behavior belongs to the owning implementation lanes."""
from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field
from servicefabric_agentic_contracts import AgentRunPlan
from servicefabric_contracts.common import Identifier, ImmutableContractModel


class _FactoryContract(ImmutableContractModel):
    model_config = ImmutableContractModel.model_config | ConfigDict(populate_by_name=True)


class ModuleTechnologySelection(_FactoryContract):
    module_id: Identifier
    primitive: str = Field(min_length=1, max_length=128)
    kit_reference: str = Field(min_length=1, max_length=512)
    adapter_id: Identifier
    runtime_family: str = Field(min_length=1, max_length=128)
    lifecycle_requirements: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    technique_policy_ids: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    resource_requirement_ids: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    provider_role: str = Field(min_length=1, max_length=128)


class TechnologyProfile(_FactoryContract):
    profile_id: Identifier
    application_blueprint_id: Identifier
    application_blueprint_version: str = Field(min_length=1, max_length=128)
    module_selections: tuple[ModuleTechnologySelection, ...] = Field(default_factory=tuple, max_length=128)
    unresolved_requirements: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=128)
    approved: bool = False


class EngineeringLane(_FactoryContract):
    lane_id: Identifier
    role: str = Field(min_length=1, max_length=128)
    module_ids: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=128)
    dependencies: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    allowed_paths: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    forbidden_paths: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    required_context: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    expected_outputs: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    verification_commands: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    provider_role: str = Field(min_length=1, max_length=128)
    integration_owned: bool = False


class EngineeringBlueprint(_FactoryContract):
    blueprint_id: Identifier
    application_id: Identifier
    application_blueprint_id: Identifier
    technology_profile_id: Identifier
    agent_run_plan: AgentRunPlan
    lanes: tuple[EngineeringLane, ...] = Field(min_length=1, max_length=128)
    integration_lane_id: Identifier
    acceptance_lane_id: Identifier
    maximum_parallel_tasks: int = Field(ge=1, le=64)


class FactoryApprovalDecision(_FactoryContract):
    decision_id: Identifier
    run_id: Identifier
    subject_ref: str = Field(min_length=1, max_length=512)
    decision: Literal["approve", "reject", "revise"]
    reason: str = Field(min_length=1, max_length=4000)
    decided_by: str = Field(min_length=1, max_length=256)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=64)


class CandidateReviewDecision(_FactoryContract):
    decision_id: Identifier
    run_id: Identifier
    task_id: Identifier
    commit_sha: str = Field(pattern=r"^[0-9a-f]{7,64}$")
    decision: Literal["accept", "reject", "rework", "escalate"]
    reason: str = Field(min_length=1, max_length=4000)
    changed_paths: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=64)


class UnmetRequirement(_FactoryContract):
    requirement_id: Identifier
    application_id: Identifier
    run_id: Identifier
    originating_task_id: Identifier | None = None
    required_behavior: str = Field(min_length=1, max_length=4000)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    proposed_scope: Literal["application", "library", "framework-kit", "primitive", "platform"]
    urgency: Literal["low", "medium", "high", "critical"]
    workaround: str | None = Field(default=None, min_length=1, max_length=4000)


class ApplicationFactoryHandoff(_FactoryContract):
    run_id: Identifier
    application_id: Identifier
    status: Literal["success", "failed", "blocked", "cancelled"]
    integration_commit: str | None = Field(default=None, pattern=r"^[0-9a-f]{7,64}$")
    agent_handoff_ref: str = Field(min_length=1, max_length=512)
    review_decision_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    unmet_requirements: tuple[UnmetRequirement, ...] = Field(default_factory=tuple, max_length=128)
    verification_evidence: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
