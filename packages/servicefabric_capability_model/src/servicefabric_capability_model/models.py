"""The stable semantic declaration of an application capability."""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field, field_validator

from servicefabric_contracts.common import Identifier, ImmutableContractModel, OperationReference
from servicefabric_contracts.effects import EffectContract


class CapabilityMetadata(ImmutableContractModel):
    """Stable identity and human-facing title for a capability."""

    id: Identifier
    title: str = Field(min_length=1, max_length=120)
    domain: Identifier


class CapabilityDefinitionSpec(ImmutableContractModel):
    """Semantic meaning of a capability and the exact operation it describes."""

    operation_ref: OperationReference = Field(
        validation_alias=AliasChoices("operationRef", "operation_ref", "operationId", "operation_id"),
        serialization_alias="operationRef",
    )
    objective: str = Field(min_length=1, max_length=4000)
    capability_class: Identifier = Field(alias="capabilityClass")
    concepts: tuple[str, ...] = Field(min_length=1, max_length=64)
    expected_inputs: tuple[str, ...] = Field(alias="expectedInputs", min_length=1, max_length=32)
    expected_outputs: tuple[str, ...] = Field(alias="expectedOutputs", min_length=1, max_length=32)
    effect_contract: EffectContract = Field(
        validation_alias=AliasChoices("effects", "effectContract", "effect_contract"),
        serialization_alias="effects",
    )
    suitable_for: tuple[str, ...] = Field(alias="suitableFor", default=(), max_length=32)
    unsuitable_for: tuple[str, ...] = Field(alias="unsuitableFor", default=(), max_length=32)
    quality_dimensions: tuple[str, ...] = Field(alias="qualityDimensions", default=(), max_length=32)

    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}

    @field_validator("concepts", "expected_inputs", "expected_outputs", "suitable_for", "unsuitable_for", "quality_dimensions")
    @classmethod
    def validate_terms(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned):
            raise ValueError("semantic terms must be non-empty")
        if len(set(value.casefold() for value in cleaned)) != len(cleaned):
            raise ValueError("semantic terms must be unique")
        return cleaned

    @property
    def effects(self) -> EffectContract:
        """Compatibility-readable name for the serialized effects contract."""

        return self.effect_contract


class CapabilityDefinition(ImmutableContractModel):
    """A stable semantic declaration, never an invocation or implementation."""

    api_version: Literal["servicefabric.local/v1"] = Field(alias="apiVersion")
    kind: Literal["CapabilityDefinition"]
    metadata: CapabilityMetadata
    spec: CapabilityDefinitionSpec

    model_config = ImmutableContractModel.model_config | {"populate_by_name": True}
