"""Stable semantic and behavioral declarations for bounded tool operations."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import Identifier, ImmutableContractModel

Determinism = Literal["deterministic", "conditionally_deterministic", "nondeterministic"]
InteractionMode = Literal["synchronous", "asynchronous", "either"]
DurationClass = Literal["short", "bounded_long", "durable"]
SideEffectClass = Literal["none", "read_only_external", "reversible", "irreversible"]


class CapabilityDeclaration(ImmutableContractModel):
    capability_id: Identifier
    summary: str = Field(min_length=1, max_length=500)
    when_to_use: tuple[str, ...] = Field(min_length=1, max_length=32)
    when_not_to_use: tuple[str, ...] = Field(min_length=1, max_length=32)


class ToolBehavior(ImmutableContractModel):
    determinism: Determinism
    side_effect_class: SideEffectClass
    interaction_mode: InteractionMode
    duration_class: DurationClass
    streaming_supported: bool
    cancellation_supported: bool
    progress_supported: bool
    human_participation: Literal["none", "optional", "required"]
