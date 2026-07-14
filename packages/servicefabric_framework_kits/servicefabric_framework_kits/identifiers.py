"""Parsing and validation of exact framework kit references."""

from __future__ import annotations

import re
from dataclasses import dataclass

from servicefabric_framework_kits.errors import InvalidKitReference


@dataclass(frozen=True)
class KitReference:
    """Represents a validated, exact reference to a framework kit."""

    kit_id: str
    version: str

    def to_string(self) -> str:
        """Returns the canonical string representation."""
        return f"{self.kit_id} @ServiceFabric/portfolio/applications/revisions/examples.hello-static-{self.version}.json"


def parse_kit_reference(val: str) -> KitReference:
    """Parses and validates a kit reference string.

    Args:
        val: Reference string e.g., 'fastapi-service @ServiceFabric/portfolio/revisions/hello-1.0.0.json'.

    Returns:
        A validated KitReference.

    Raises:
        InvalidKitReference: If the reference string is malformed or unparseable.
    """
    if not isinstance(val, str):
        raise InvalidKitReference("Kit reference must be a string.")
    
    if " @ServiceFabric/" not in val:
        raise InvalidKitReference(
            f"Invalid kit reference '{val}': must be formatted as 'kit_id @ServiceFabric/path'."
        )

    parts = val.split(" @ServiceFabric/", 1)
    kit_id = parts[0].strip()
    path = parts[1].strip()

    # Verify kit_id format
    from servicefabric_application_model.loader import ID_PATTERN
    if not ID_PATTERN.match(kit_id):
        raise InvalidKitReference(f"Invalid kit ID '{kit_id}' in reference.")

    # Extract version suffix from the path, e.g., 'examples.hello-static-1.0.0.json' -> '1.0.0'
    match = re.search(r"[-_](\d+\.\d+\.\d+(?:-\w+)?)\.json$", path)
    if not match:
        raise InvalidKitReference(f"Cannot parse version from kit path: '{path}'.")
    version = match.group(1)

    return KitReference(kit_id=kit_id, version=version)
