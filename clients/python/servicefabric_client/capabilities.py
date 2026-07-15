"""Static Wave-4 capability composition for generated applications.

This module deliberately has no invocation, runtime, or consumer-projection
behavior.  It reads reviewed declarations, validates their local references,
and delegates persistence to the capability registry public API.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from servicefabric_capability_model import CapabilityDefinition
from servicefabric_capability_registry import (
    CapabilityConflictError,
    CapabilityNotFoundError,
    CapabilityRecord,
    CapabilityRegistry,
    capability_content_digest,
)
from servicefabric_operation_model import OperationDefinition, load_operation_definition
from servicefabric_workspace import ApplicationLayout, WorkspaceLayout, validate_application_id


class CapabilityValidationError(ValueError):
    """Raised when generated static capability declarations are inconsistent."""


@dataclass(frozen=True)
class ValidatedCapabilities:
    """Static declarations that have resolved every local reference."""

    application_id: str
    operations: tuple[OperationDefinition, ...]
    capabilities: tuple[CapabilityDefinition, ...]


def registry_for_workspace(layout: WorkspaceLayout) -> CapabilityRegistry:
    """Return the workspace-local registry for static definitions only."""

    return CapabilityRegistry(layout.registry / "capabilities")


def validate_generated_capabilities(
    workspace: WorkspaceLayout, application_id: str
) -> ValidatedCapabilities:
    """Load and validate generated declarations without mutating registry state."""

    app_id = validate_application_id(application_id)
    application = ApplicationLayout.from_application_id(app_id, workspace.applications)
    if not application.root.is_dir():
        raise CapabilityValidationError(f"application '{app_id}' does not exist in this workspace")

    app_manifest = _read_object(application.application_definition, "application declaration")
    if app_manifest.get("kind") != "Application":
        raise CapabilityValidationError("application declaration must have kind Application")
    if app_manifest.get("metadata", {}).get("id") != app_id:
        raise CapabilityValidationError("application declaration identity does not match the requested application")
    declared_modules = app_manifest.get("spec", {}).get("modules")
    if not isinstance(declared_modules, list) or not all(isinstance(item, str) for item in declared_modules):
        raise CapabilityValidationError("application declaration must list its module identities")

    modules = _load_modules(application, app_id, set(declared_modules))
    schema_ids = _load_schema_ids(application.root / ".servicefabric" / "schemas")
    operations = _load_operations(application.root / ".servicefabric" / "operations", app_id, modules, schema_ids)
    capabilities = _load_capabilities(application.root / ".servicefabric" / "capabilities", operations)
    return ValidatedCapabilities(app_id, operations, capabilities)


def register_generated_capabilities(
    workspace: WorkspaceLayout, application_id: str
) -> tuple[CapabilityRecord, ...]:
    """Validate then register all declarations deterministically and idempotently."""

    validated = validate_generated_capabilities(workspace, application_id)
    registry = registry_for_workspace(workspace)

    # Detect every identity conflict before the first write so a conflicting
    # application registration cannot leave a partial new registration behind.
    for definition in validated.capabilities:
        try:
            existing = registry.describe(definition.metadata.id)
        except CapabilityNotFoundError:
            continue
        if existing.digest != capability_content_digest(definition):
            raise CapabilityConflictError(
                f"capability '{definition.metadata.id}' is already registered with different content"
            )

    return tuple(
        registry.register(definition, validated.application_id).record
        for definition in validated.capabilities
    )


def _read_object(path: Path, label: str) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise CapabilityValidationError(f"{label} is missing or unsafe: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityValidationError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise CapabilityValidationError(f"{label} must be a JSON object: {path}")
    return value


def _load_modules(
    application: ApplicationLayout, application_id: str, declared_modules: set[str]
) -> dict[str, set[str]]:
    modules: dict[str, set[str]] = {}
    for path in sorted(application.modules.glob("*/module.yaml")):
        value = _read_object(path, "module declaration")
        metadata = value.get("metadata")
        spec = value.get("spec")
        if not isinstance(metadata, dict) or not isinstance(spec, dict):
            raise CapabilityValidationError(f"module declaration is incomplete: {path}")
        module_id = metadata.get("id")
        if not isinstance(module_id, str) or not module_id:
            raise CapabilityValidationError(f"module declaration has no identity: {path}")
        provides = spec.get("provides", [])
        if not isinstance(provides, list):
            raise CapabilityValidationError(f"module provides must be a list: {path}")
        interfaces = {
            item["id"]
            for item in provides
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        if module_id not in declared_modules:
            raise CapabilityValidationError(
                f"module '{module_id}' is not referenced by the application declaration"
            )
        modules[module_id] = interfaces
    if not modules:
        raise CapabilityValidationError(f"application '{application_id}' has no generated modules")
    return modules


def _load_schema_ids(directory: Path) -> set[str]:
    if not directory.is_dir() or directory.is_symlink():
        raise CapabilityValidationError("generated schema directory is missing or unsafe")
    schema_ids: set[str] = set()
    for path in sorted(directory.glob("*.schema.json")):
        value = _read_object(path, "schema declaration")
        schema_id = value.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise CapabilityValidationError(f"schema declaration has no $id: {path}")
        if schema_id in schema_ids:
            raise CapabilityValidationError(f"duplicate generated schema $id: {schema_id}")
        schema_ids.add(schema_id)
    if not schema_ids:
        raise CapabilityValidationError("generated schema directory has no declarations")
    return schema_ids


def _load_operations(
    directory: Path,
    application_id: str,
    modules: dict[str, set[str]],
    schema_ids: set[str],
) -> tuple[OperationDefinition, ...]:
    if not directory.is_dir() or directory.is_symlink():
        raise CapabilityValidationError("generated operation directory is missing or unsafe")
    operations: list[OperationDefinition] = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            operation = load_operation_definition(path)
        except Exception as exc:
            raise CapabilityValidationError(f"invalid operation declaration: {path}") from exc
        if operation.application_ref != application_id:
            raise CapabilityValidationError(f"operation '{operation.operation_id}' references another application")
        if operation.module_ref not in modules:
            raise CapabilityValidationError(f"operation '{operation.operation_id}' references an unknown module")
        if operation.interface_ref not in modules[operation.module_ref]:
            raise CapabilityValidationError(f"operation '{operation.operation_id}' references an unknown interface")
        for binding in operation.bindings:
            for schema_ref in (binding.request_schema_ref, binding.response_schema_ref):
                if schema_ref is not None and schema_ref not in schema_ids:
                    raise CapabilityValidationError(
                        f"operation '{operation.operation_id}' references an unknown schema '{schema_ref}'"
                    )
        operations.append(operation)
    identifiers = [operation.operation_id for operation in operations]
    if not operations or len(set(identifiers)) != len(identifiers):
        raise CapabilityValidationError("generated operation identities must be present and unique")
    return tuple(sorted(operations, key=lambda item: item.operation_id))


def _load_capabilities(
    directory: Path, operations: tuple[OperationDefinition, ...]
) -> tuple[CapabilityDefinition, ...]:
    if not directory.is_dir() or directory.is_symlink():
        raise CapabilityValidationError("generated capability directory is missing or unsafe")
    operation_ids = {operation.operation_id for operation in operations}
    capabilities: list[CapabilityDefinition] = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            definition = CapabilityDefinition.model_validate(_read_object(path, "capability declaration"))
        except Exception as exc:
            raise CapabilityValidationError(f"invalid capability declaration: {path}") from exc
        if definition.spec.operation_ref not in operation_ids:
            raise CapabilityValidationError(
                f"capability '{definition.metadata.id}' references an unknown operation"
            )
        capabilities.append(definition)
    identifiers = [definition.metadata.id for definition in capabilities]
    if not capabilities or len(set(identifiers)) != len(identifiers):
        raise CapabilityValidationError("generated capability identities must be present and unique")
    return tuple(sorted(capabilities, key=lambda item: item.metadata.id))
