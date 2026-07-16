"""Strict contracts only; this module deliberately contains no runtime behavior."""
from __future__ import annotations

from typing import Any, Literal, Protocol
from pydantic import ConfigDict, Field
from servicefabric_contracts.common import Identifier, ImmutableContractModel


class _AgentContract(ImmutableContractModel):
    model_config = ImmutableContractModel.model_config | ConfigDict(populate_by_name=True)


class ApplicationIntent(_AgentContract):
    intent_id: Identifier
    mode: Literal["create", "modify", "debug"]
    objective: str = Field(min_length=1, max_length=4000)
    application_id: Identifier | None = None
    constraints: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    requested_capabilities: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)


class AgentTask(_AgentContract):
    task_id: Identifier
    role: str = Field(min_length=1, max_length=128)
    objective: str = Field(min_length=1, max_length=4000)
    dependencies: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    allowed_paths: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    forbidden_paths: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    required_context: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    expected_outputs: tuple[str, ...] = Field(default_factory=tuple, max_length=128)
    verification_commands: tuple[str, ...] = Field(default_factory=tuple, max_length=32)


class AgentRunPlan(_AgentContract):
    run_id: Identifier
    intent: ApplicationIntent
    tasks: tuple[AgentTask, ...] = Field(min_length=1, max_length=128)
    maximum_parallel_tasks: int = Field(ge=1, le=64)


class VerificationEvidence(_AgentContract):
    command: str = Field(min_length=1, max_length=1000)
    exit_code: int = Field(ge=0, le=255)
    summary: str = Field(min_length=1, max_length=4000)
    artifact_ref: str | None = Field(default=None, min_length=1, max_length=512)


class AgentTaskResult(_AgentContract):
    task_id: Identifier
    status: Literal["pending", "running", "success", "failed", "blocked", "cancelled"]
    changed_paths: tuple[str, ...] = Field(default_factory=tuple, max_length=256)
    commit_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{7,64}$")
    evidence: tuple[VerificationEvidence, ...] = Field(default_factory=tuple, max_length=64)
    blockers: tuple[str, ...] = Field(default_factory=tuple, max_length=64)


class AgentHandoff(_AgentContract):
    run_id: Identifier
    status: Literal["pending", "running", "success", "failed", "blocked", "cancelled"]
    task_results: tuple[AgentTaskResult, ...] = Field(default_factory=tuple, max_length=128)
    unresolved_blockers: tuple[str, ...] = Field(default_factory=tuple, max_length=128)


class AgentToolResult(_AgentContract):
    status: Literal["success", "failed", "blocked"]
    summary: str = Field(min_length=1, max_length=4000)
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: tuple[VerificationEvidence, ...] = Field(default_factory=tuple)


class CodingAgentHarness(Protocol):
    def prepare_task(self, task: AgentTask, repository: str) -> dict[str, Any]: ...
    def render_task(self, task: AgentTask) -> str: ...
    def launch_task(self, task: AgentTask) -> str: ...
    def collect_result(self, task_id: str) -> AgentTaskResult: ...
    def cancel_task(self, task_id: str) -> None: ...


class AgentTool(Protocol):
    def invoke(self, name: str, arguments: dict[str, Any]) -> AgentToolResult: ...
