"""Stable desired lifecycle declarations for tool definitions."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from .common import ImmutableContractModel, ToolIdentifier


class ToolLifecycleDeclaration(ImmutableContractModel):
    maturity: Literal["experimental", "alpha", "beta", "stable", "deprecated"]
    deprecation_status: Literal["active", "deprecated", "retired"]
    replacement_tool_ref: ToolIdentifier | None = None
    support_status: Literal["supported", "best_effort", "unsupported"]

    @model_validator(mode="after")
    def validate_replacement(self) -> "ToolLifecycleDeclaration":
        if self.deprecation_status == "deprecated" and not self.replacement_tool_ref:
            raise ValueError("deprecated tools require a replacement reference")
        if self.deprecation_status != "deprecated" and self.replacement_tool_ref:
            raise ValueError("replacement references are only valid for deprecated tools")
        return self
