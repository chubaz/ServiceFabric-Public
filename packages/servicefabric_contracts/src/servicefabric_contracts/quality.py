"""References to evaluation suites and publication quality gates."""

from __future__ import annotations

from pydantic import Field, field_validator

from .common import Identifier, ImmutableContractModel


class QualityGateReference(ImmutableContractModel):
    gate_id: Identifier
    suite_ref: str = Field(min_length=3, max_length=256, pattern=r"^suite://[a-z][a-z0-9._:/-]+$")
    required: bool = True


class QualityDeclaration(ImmutableContractModel):
    evaluation_suite_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    agent_callability_suite_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    quality_gates: tuple[QualityGateReference, ...] = Field(default_factory=tuple, max_length=32)

    @field_validator("evaluation_suite_refs", "agent_callability_suite_refs")
    @classmethod
    def validate_suite_refs(cls, references: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(references)) != len(references):
            raise ValueError("suite references must be unique")
        if any(not reference.startswith("suite://") for reference in references):
            raise ValueError("quality suites must be opaque suite references")
        return references
