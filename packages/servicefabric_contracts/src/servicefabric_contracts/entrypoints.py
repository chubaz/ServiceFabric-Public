"""Entrypoints describe how a package can be reached, not tool contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from .common import ContractModel, Identifier
from .exposure import ExposureDeclaration, validate_exposure_set

EntrypointKind = Literal["http_api", "cli", "web_ui", "worker", "graph", "mcp_server", "library"]


class EntrypointDeclaration(ContractModel):
    id: Identifier
    kind: EntrypointKind
    description: str = Field(min_length=1, max_length=2000)
    runtime_ref: str = Field(min_length=1, max_length=256, pattern=r"^[a-z][a-z0-9._:/-]+$")
    machine_callable: bool
    may_produce_effects: bool
    exposures: list[ExposureDeclaration] = Field(min_length=1, max_length=8)
    health_ref: Identifier | None = None

    @field_validator("exposures")
    @classmethod
    def validate_exposures(cls, exposures: list[ExposureDeclaration]) -> list[ExposureDeclaration]:
        validate_exposure_set(exposures)
        return exposures
