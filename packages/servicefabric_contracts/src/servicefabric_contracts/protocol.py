"""Secret-free protocol origin metadata."""
from typing import Literal
from pydantic import Field, field_validator
from .common import ContractModel, Identifier, has_secret_like_key

class ProtocolContext(ContractModel):
    protocol: Literal["internal", "http", "cli", "graph", "scheduled", "mcp", "federated_mcp"]
    adapter_ref: Identifier
    session_ref: Identifier | None = None
    remote_request_ref: Identifier | None = None
    client_ref: Identifier | None = None
    projection_metadata: dict[str, str] = Field(default_factory=dict, max_length=16)

    @field_validator("projection_metadata")
    @classmethod
    def safe_metadata(cls, value):
        if any(has_secret_like_key(k) or k.lower() in {"authorization", "cookie", "set-cookie"} for k in value):
            raise ValueError("protocol metadata cannot contain credentials or transport headers")
        return dict(sorted(value.items()))
