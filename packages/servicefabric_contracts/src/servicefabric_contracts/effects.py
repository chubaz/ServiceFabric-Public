"""Prospective effect declarations used as policy inputs."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .common import Identifier, ImmutableContractModel

EffectType = Literal[
    "none",
    "external_read",
    "database_read",
    "database_write",
    "file_write",
    "message_send",
    "task_create",
    "payment_initiate",
    "infrastructure_change",
    "human_workflow_create",
]
Reversibility = Literal["not_applicable", "reversible", "compensatable", "irreversible"]


class EffectDeclaration(ImmutableContractModel):
    effect_type: EffectType
    target_category: Identifier
    scope: str = Field(min_length=1, max_length=256)
    reversibility: Reversibility
    verification_required: bool
    approval_required: bool
    idempotency_required: bool

    @model_validator(mode="after")
    def validate_none_effect(self) -> "EffectDeclaration":
        non_mutating = {"none", "external_read", "database_read"}
        if self.effect_type in non_mutating and self.reversibility != "not_applicable":
            raise ValueError("non-mutating effects must use not_applicable reversibility")
        if self.effect_type not in non_mutating and self.reversibility == "not_applicable":
            raise ValueError("mutating effects require explicit reversibility")
        return self


class EffectContract(ImmutableContractModel):
    effects: tuple[EffectDeclaration, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def validate_effect_set(self) -> "EffectContract":
        types = [effect.effect_type for effect in self.effects]
        if "none" in types and len(types) != 1:
            raise ValueError("none effect cannot coexist with effectful declarations")
        if len(set(types)) != len(types):
            raise ValueError("effect types must be unique")
        return self

    @property
    def is_effectful(self) -> bool:
        return self.effects[0].effect_type != "none"
