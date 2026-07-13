"""Defines valid ServiceFabric primitives and kinds."""

from __future__ import annotations

from typing import Literal

from servicefabric_application_model.errors import InvalidPrimitive

PrimitiveKind = Literal["service", "web", "worker", "job", "library"]

VALID_PRIMITIVES: set[PrimitiveKind] = {"service", "web", "worker", "job", "library"}


def validate_primitive(primitive: str) -> PrimitiveKind:
    """Validates if a given string is a valid ServiceFabric primitive.

    Raises:
        InvalidPrimitive: If the primitive is not recognized.
    """
    if primitive not in VALID_PRIMITIVES:
        raise InvalidPrimitive(
            f"Invalid primitive kind '{primitive}'. "
            f"Must be one of: {', '.join(sorted(VALID_PRIMITIVES))}"
        )
    return primitive  # type: ignore
