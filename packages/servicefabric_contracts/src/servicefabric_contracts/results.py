from datetime import datetime, timedelta
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .common import ContractModel, Identifier, ToolIdentifier, is_json_value
from .effect_receipt import EffectReceiptSpec
from .errors import ToolError
from .evidence import EvidenceRecord
from .warnings import ToolWarning
class ToolResult(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["ToolResult"]
    status: Literal["success", "partial", "error"]
    invocation_id: Identifier
    tool_id: ToolIdentifier
    revision_ref: str
    started_at: datetime
    completed_at: datetime
    duration: timedelta
    data: object | None = None
    error: ToolError | None = None
    warnings: tuple[ToolWarning, ...] = Field(default_factory=tuple, max_length=64)
    evidence: tuple[EvidenceRecord, ...] = Field(default_factory=tuple, max_length=128)
    effect_receipts: tuple[EffectReceiptSpec, ...] = Field(default_factory=tuple, max_length=64)
    meta: dict[str, object] = Field(default_factory=dict, max_length=32)
    model_config = ContractModel.model_config | {"populate_by_name": True}
    @field_validator("started_at", "completed_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError("result timestamps must be timezone-aware")
        return value
    @field_validator("data", "meta")
    @classmethod
    def json_payload(cls, value):
        if not is_json_value(value): raise ValueError("result payloads must be JSON-compatible")
        return value
    @model_validator(mode="after")
    def status_consistency(self):
        if self.completed_at < self.started_at: raise ValueError("completion cannot precede start")
        if self.status == "success" and self.error: raise ValueError("success cannot contain a primary error")
        if self.status == "partial" and not (self.data is not None or self.evidence or self.effect_receipts): raise ValueError("partial results require usable output")
        if self.status == "partial" and not (self.error or self.warnings): raise ValueError("partial results must explain incompleteness")
        if self.status == "error" and not self.error: raise ValueError("error results require ToolError")
        return self
