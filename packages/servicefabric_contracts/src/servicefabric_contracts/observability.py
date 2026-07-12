"""Declarative observability requirements."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import Identifier, ImmutableContractModel


class ObservabilityDeclaration(ImmutableContractModel):
    audit_level: Literal["none", "metadata", "full"]
    trace_required: bool
    evidence_required: bool
    metric_categories: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=32)
