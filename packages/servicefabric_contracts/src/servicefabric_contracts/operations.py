from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .common import ContractModel, Identifier, ToolIdentifier
from .errors import ToolError
from .metadata import ResourceMetadata
class CancellationState(ContractModel):
    cancellable: bool
    cancellation_requested_at: datetime | None = None
    cancellation_reason: str | None = Field(default=None, max_length=1000)
    cancellation_state: Literal["not_requested", "requested", "acknowledged", "completed", "rejected"] = "not_requested"
class OperationCondition(ContractModel):
    type: Identifier
    status: Literal["true", "false", "unknown"]
    reason: Identifier
    message: str = Field(min_length=1, max_length=1000)
    observed_at: datetime
class ServiceFabricOperationSpec(ContractModel):
    operation_id: Identifier
    request_ref: Identifier
    invocation_ref: Identifier
    tool_id: ToolIdentifier
    revision_ref: str
    state: Literal["accepted", "queued", "running", "waiting_for_approval", "waiting_for_dependency", "waiting_for_human", "succeeded", "partially_succeeded", "failed", "cancelled", "timed_out"]
    progress: int | None = Field(default=None, ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    result_ref: Identifier | None = None
    error: ToolError | None = None
    cancellation: CancellationState
    conditions: tuple[OperationCondition, ...] = Field(default_factory=tuple, max_length=64)
    @model_validator(mode="after")
    def state_consistency(self):
        terminal={"succeeded","partially_succeeded","failed","cancelled","timed_out"}
        if (self.state in terminal) != (self.completed_at is not None): raise ValueError("terminal states require completed_at")
        if self.state not in terminal and self.result_ref: raise ValueError("non-terminal operations cannot contain final results")
        if self.state == "failed" and not self.error: raise ValueError("failed operations require ToolError")
        if self.state == "succeeded" and self.error: raise ValueError("succeeded operations cannot contain errors")
        if self.state in {"cancelled","timed_out"} and not self.cancellation.cancellation_reason: raise ValueError("cancelled and timed-out operations require a reason")
        return self
class ServiceFabricOperation(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ServiceFabricOperation"]
    metadata: ResourceMetadata
    spec: ServiceFabricOperationSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}
