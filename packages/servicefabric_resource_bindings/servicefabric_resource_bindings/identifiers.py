"""Identifier helpers for resource binding environment injection."""

from __future__ import annotations

import re

from servicefabric_resource_bindings.errors import InvalidResourceBinding

_RESOURCE_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_ENVIRONMENT_KEY = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")


def validate_resource_id(value: str, field: str = "resource id") -> str:
    """Validate the resource id subset accepted for local binding plans."""

    if not isinstance(value, str) or not _RESOURCE_ID.fullmatch(value):
        raise InvalidResourceBinding(
            f"{field} must start with a lowercase letter and contain only "
            "lowercase letters, digits, or hyphens"
        )
    return value


def validate_environment_key(value: str, field: str = "environment key") -> str:
    """Validate environment variable names before publishing a binding plan."""

    if not isinstance(value, str) or not _ENVIRONMENT_KEY.fullmatch(value):
        raise InvalidResourceBinding(
            f"{field} must contain only uppercase letters, digits, or underscores"
        )
    return value


def environment_key_for(resource_id: str, suffix: str) -> str:
    """Return the deterministic ServiceFabric environment key for a binding."""

    validate_resource_id(resource_id)
    if not isinstance(suffix, str) or not suffix or not suffix.replace("_", "").isalnum():
        raise InvalidResourceBinding("environment key suffix is invalid")
    suffix_key = suffix.upper()
    return validate_environment_key(
        f"SF_{resource_id.replace('-', '_').upper()}_{suffix_key}"
    )
