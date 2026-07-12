"""Shared validation primitives for declarative contract resources."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


IDENTIFIER_PATTERN = r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
SEMVER_PATTERN = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
SECRET_KEY_PATTERN = re.compile(r"(?:password|secret|token|api[_-]?key|credential)", re.IGNORECASE)

Identifier = Annotated[str, Field(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN)]
OperationReference = Annotated[str, Field(min_length=3, max_length=160, pattern=IDENTIFIER_PATTERN)]
ToolIdentifier = Annotated[
    str,
    Field(min_length=3, max_length=128, pattern=r"^[a-z][a-z0-9_-]{0,62}\.[a-z][a-z0-9_]{0,62}$"),
]
Digest = Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")]


class ContractModel(BaseModel):
    """Strict base model: contracts are source-controlled public declarations."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)


class ImmutableContractModel(ContractModel):
    """Base for immutable revision content and its nested declarations."""

    model_config = ContractModel.model_config | {"frozen": True}


def has_secret_like_key(value: str) -> bool:
    return SECRET_KEY_PATTERN.search(value) is not None


def is_json_value(value: object) -> bool:
    if value is None or isinstance(value, (str, bool, int, float)):
        return True
    if isinstance(value, list):
        return all(is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())
    return False
