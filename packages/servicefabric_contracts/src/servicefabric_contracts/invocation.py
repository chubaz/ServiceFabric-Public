from datetime import datetime
from typing import Annotated, Literal, Union
from pydantic import Field, field_validator
from .budgets import ExecutionBudget
from .caller import CallerContext
from .common import ContractModel, Digest, Identifier, ToolIdentifier, is_json_value
from .execution_context import ParentExecutionContext
from .metadata import ResourceMetadata
from .protocol import ProtocolContext
class DeploymentInvocationTarget(ContractModel):
    target_kind: Literal["deployment"]
    tool_id: ToolIdentifier
    deployment_ref: Identifier
class RevisionInvocationTarget(ContractModel):
    target_kind: Literal["revision"]
    tool_id: ToolIdentifier
    revision_ref: str = Field(pattern=r"^[a-z0-9][a-z0-9._:-]+$")
    @field_validator("revision_ref")
    @classmethod
    def immutable_revision(cls, value):
        if value in {"latest", "current", "production"}: raise ValueError("revision target cannot be a mutable alias")
        return value
ToolInvocationTarget = Annotated[Union[DeploymentInvocationTarget, RevisionInvocationTarget], Field(discriminator="target_kind")]
class InvocationIdempotency(ContractModel):
    key_digest: Digest
    scope: Literal["caller", "tenant", "deployment", "tool"]
    replay_policy: Literal["return_previous", "reject_duplicate", "resume"]
    caller_intent: str = Field(min_length=1, max_length=256)
class ToolInvocationRequestSpec(ContractModel):
    request_id: Identifier
    target: ToolInvocationTarget
    arguments: dict[str, object] = Field(default_factory=dict, max_length=256)
    caller_context: CallerContext
    protocol_context: ProtocolContext
    parent_context: ParentExecutionContext | None = None
    budget: ExecutionBudget
    idempotency: InvocationIdempotency | None = None
    approval_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=32)
    requested_response_mode: Literal["synchronous", "durable", "either"] = "either"
    client_metadata: dict[str, str] = Field(default_factory=dict, max_length=16)
    @field_validator("arguments")
    @classmethod
    def json_arguments(cls, value):
        if not is_json_value(value): raise ValueError("arguments must be JSON-compatible")
        return value
class ToolInvocationRequest(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolInvocationRequest"]
    metadata: ResourceMetadata
    spec: ToolInvocationRequestSpec
    model_config = ContractModel.model_config | {"populate_by_name": True}
class ToolInvocationAcceptance(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolInvocationAcceptance"]
    request_id: Identifier
    invocation_id: Identifier
    operation_ref: Identifier
    accepted_at: datetime
    status: Literal["accepted", "queued", "deferred"]
    progress_projection_ref: Identifier | None = None
    model_config = ContractModel.model_config | {"populate_by_name": True}
    @field_validator("accepted_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError("acceptance timestamp must be timezone-aware")
        return value
