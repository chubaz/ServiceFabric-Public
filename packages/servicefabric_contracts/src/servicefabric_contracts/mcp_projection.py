"""Optional declarative MCP projection metadata; never an execution owner."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .common import ImmutableContractModel


class McpAnnotations(ImmutableContractModel):
    read_only_hint: bool
    destructive_hint: bool
    idempotent_hint: bool
    open_world_hint: bool


class McpProjection(ImmutableContractModel):
    expose: bool = False
    name_override: str | None = Field(default=None, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.\-/]+$")
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=1000)
    annotations: McpAnnotations | None = None
    structured_result_support: bool = True
    progress_projection: Literal["disabled", "when_negotiated"] = "disabled"
    durable_operation_projection: Literal["disabled", "when_negotiated"] = "disabled"

    @model_validator(mode="after")
    def validate_hidden_projection(self) -> "McpProjection":
        projection_fields = (self.name_override, self.title, self.description, self.annotations)
        if not self.expose and (any(value is not None for value in projection_fields) or self.progress_projection != "disabled" or self.durable_operation_projection != "disabled"):
            raise ValueError("disabled MCP projection cannot declare projection metadata")
        return self
