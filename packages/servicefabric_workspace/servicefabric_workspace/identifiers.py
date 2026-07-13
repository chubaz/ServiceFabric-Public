"""Validation and typing of workspace identifiers."""

from __future__ import annotations

import re

from servicefabric_workspace.errors import InvalidApplicationId

# Regular expression matching lowercase letters, numbers, and single hyphens,
# starting with a letter and ending with a letter or number.
APPLICATION_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def validate_application_id(application_id: str) -> str:
    """Validates an application ID against naming and length constraints.

    Returns:
        The validated application ID if successful.

    Raises:
        InvalidApplicationId: If the ID does not meet requirements.
    """
    if not application_id:
        raise InvalidApplicationId("Application ID cannot be empty")

    length = len(application_id)
    if length < 3 or length > 63:
        raise InvalidApplicationId(
            f"Application ID '{application_id}' length must be between 3 and 63 characters (got {length})"
        )

    if not APPLICATION_ID_PATTERN.match(application_id):
        raise InvalidApplicationId(
            f"Application ID '{application_id}' is invalid. It must consist only of lowercase letters, "
            f"numbers, and single hyphens, start with a letter, and end with a letter or number."
        )

    return application_id
