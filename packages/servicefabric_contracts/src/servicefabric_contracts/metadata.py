"""Framework-neutral resource metadata."""

from __future__ import annotations

import re

from pydantic import Field, field_validator

from .common import ContractModel, IDENTIFIER_PATTERN, Identifier, has_secret_like_key


class OwnerReference(ContractModel):
    kind: str = Field(min_length=1, max_length=32, pattern=r"^[a-z][a-z0-9_-]*$")
    id: Identifier


class ResourceMetadata(ContractModel):
    id: Identifier
    name: str = Field(min_length=1, max_length=120)
    namespace: Identifier | None = None
    description: str = Field(min_length=1, max_length=4000)
    labels: dict[str, str] = Field(default_factory=dict, max_length=32)
    annotations: dict[str, str] = Field(default_factory=dict, max_length=32)
    owner_ref: OwnerReference

    @field_validator("labels", "annotations")
    @classmethod
    def validate_metadata_map(cls, values: dict[str, str]) -> dict[str, str]:
        for key, value in values.items():
            if not key or len(key) > 96 or not value or len(value) > 512:
                raise ValueError("metadata keys and values must be bounded and non-empty")
            if re.fullmatch(IDENTIFIER_PATTERN, key) is None:
                raise ValueError("metadata keys must be normalized identifiers")
            if has_secret_like_key(key):
                raise ValueError("metadata must not contain credential material")
        return dict(sorted(values.items()))
