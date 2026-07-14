"""Strict validation enforcement for modules inside framework kits."""

from __future__ import annotations

from servicefabric_application_model import ModuleDefinition
from servicefabric_framework_kits.errors import KitValidationError
from servicefabric_framework_kits.protocol import FrameworkKitAdapter


def require_valid_module(
    adapter: FrameworkKitAdapter,
    module: ModuleDefinition,
) -> None:
    """Enforces that a module definition is fully valid according to the kit's adapter.

    Raises:
        KitValidationError: If any validation errors are detected.
    """
    findings = adapter.validate_module(module)
    errors = tuple(finding for finding in findings if finding.severity == "error")
    if errors:
        error_messages = "; ".join(finding.message for finding in errors)
        raise KitValidationError(
            f"Module '{module.module_id}' kit validation failed: {error_messages}"
        )
