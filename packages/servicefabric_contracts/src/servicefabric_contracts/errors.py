"""Stable caller-safe invocation errors."""
import re
from datetime import timedelta
from typing import Literal
from pydantic import Field, field_validator, model_validator
from .common import ContractModel, Identifier, has_secret_like_key

ERROR_CODE = re.compile(r"^SF-(AUTHN|AUTHZ|DELEGATION|APPROVAL|VALID|POLICY|BUDGET|EXEC|DEPEND|OUTPUT|EFFECT|QUALITY|MCP|RUNTIME)-[A-Z0-9_]+$")
class ToolError(ContractModel):
    code: str = Field(min_length=8, max_length=96)
    category: Literal["authentication", "authorization", "delegation", "approval", "validation", "policy", "budget", "execution", "dependency", "output", "effect", "quality", "mcp", "runtime"]
    message: str = Field(min_length=1, max_length=1000)
    retryable: bool = False
    retry_classification: Literal["transient", "throttled", "dependency_recovery", "manual_review"] | None = None
    retry_after: timedelta | None = None
    details: dict[str, object] = Field(default_factory=dict, max_length=32)
    dependency_ref: Identifier | None = None
    cause_ref: Identifier | None = None
    correlation_ref: Identifier | None = None

    @field_validator("code")
    @classmethod
    def valid_code(cls, value):
        if not ERROR_CODE.fullmatch(value): raise ValueError("invalid ServiceFabric error namespace")
        return value
    @field_validator("details")
    @classmethod
    def safe_details(cls, value):
        if any(has_secret_like_key(str(k)) for k in value): raise ValueError("error details cannot contain credentials")
        return value
    @model_validator(mode="after")
    def retry_consistency(self):
        if self.retryable != (self.retry_classification is not None): raise ValueError("retryable errors require a retry classification")
        return self
