from datetime import datetime
from pydantic import Field, field_validator
from .budgets import ExecutionBudget
from .caller import CallerContext
from .common import ContractModel, Identifier, ToolIdentifier
class ParentExecutionContext(ContractModel):
    parent_invocation_ref: Identifier | None = None
    parent_operation_ref: Identifier | None = None
    graph_execution_ref: Identifier | None = None
    root_correlation_id: Identifier
    depth: int = Field(ge=0, le=64)
    delegated_authority_ref: Identifier | None = None
    inherited_budget_ref: Identifier | None = None
class ToolExecutionContext(ContractModel):
    invocation_id: Identifier
    resolved_tool_id: ToolIdentifier
    resolved_revision_ref: str = Field(pattern=r"^[a-z0-9][a-z0-9._:-]+$")
    deployment_ref: Identifier | None = None
    caller_context: CallerContext
    effective_budget: ExecutionBudget
    deadline: datetime | None = None
    cancellation_ref: Identifier | None = None
    trace_context_ref: Identifier
    approval_refs: tuple[Identifier, ...] = Field(default_factory=tuple)
    policy_decision_refs: tuple[Identifier, ...] = Field(default_factory=tuple)
    credential_binding_refs: tuple[Identifier, ...] = Field(default_factory=tuple)
    parent_context: ParentExecutionContext | None = None
    @field_validator("resolved_revision_ref")
    @classmethod
    def immutable_revision(cls, value):
        if value in {"latest", "current", "production"}: raise ValueError("resolved revisions cannot be aliases")
        return value
