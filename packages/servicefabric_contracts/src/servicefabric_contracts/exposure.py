"""Protocol-neutral exposure declarations."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .common import ContractModel, OperationReference

ExposureKind = Literal["internal", "web", "cli", "scheduled", "mcp", "none"]


class ExposureDeclaration(ContractModel):
    kind: ExposureKind
    operation_refs: list[OperationReference] = Field(default_factory=list, max_length=64)

    @model_validator(mode="after")
    def validate_operation_references(self) -> "ExposureDeclaration":
        if self.kind == "mcp" and not self.operation_refs:
            raise ValueError("MCP exposure requires at least one bounded operation reference")
        if self.kind != "mcp" and self.operation_refs:
            raise ValueError("operation references are only declared for MCP exposure")
        if len(set(self.operation_refs)) != len(self.operation_refs):
            raise ValueError("operation references must be unique")
        return self


def validate_exposure_set(exposures: list[ExposureDeclaration]) -> None:
    kinds = [exposure.kind for exposure in exposures]
    if not kinds:
        raise ValueError("an entrypoint must declare at least one exposure")
    if "none" in kinds and len(kinds) != 1:
        raise ValueError("none exposure cannot coexist with another exposure")
    if len(set(kinds)) != len(kinds):
        raise ValueError("exposure kinds must be unique")
