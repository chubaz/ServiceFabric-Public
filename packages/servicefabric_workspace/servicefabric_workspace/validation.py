"""Validation levels for ServiceFabric Workspaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from servicefabric_workspace.errors import InvalidApplicationId
from servicefabric_workspace.identifiers import validate_application_id
from servicefabric_workspace.models import ValidationFinding, WorkspaceLayout, WorkspaceValidation


def validate_workspace_structural(layout: WorkspaceLayout) -> WorkspaceValidation:
    """Performs structural (fast) checks on the workspace layout.

    Verifies existences of base paths, registry files, and path scopes without heavy file parsing.
    """
    findings: list[ValidationFinding] = []

    # 1. Check workspace root and state directory presence
    if not layout.root.is_dir():
        findings.append(
            ValidationFinding(
                code="missing_root",
                severity="error",
                path=layout.root,
                message="Workspace root directory does not exist.",
            )
        )
    if not layout.state.is_dir():
        findings.append(
            ValidationFinding(
                code="missing_state",
                severity="error",
                path=layout.state,
                message="Platform state directory (.servicefabric) does not exist.",
            )
        )

    # 2. Check metadata workspace.yaml existence and header kind
    workspace_yaml_path = layout.root / "workspace.yaml"
    if not workspace_yaml_path.is_file():
        findings.append(
            ValidationFinding(
                code="missing_workspace_yaml",
                severity="error",
                path=workspace_yaml_path,
                message="Workspace configuration file 'workspace.yaml' is missing.",
            )
        )
    else:
        try:
            # Safely check metadata without requiring external yaml package if possible,
            # but using standard YAML parser is safer for accuracy.
            import yaml
            with workspace_yaml_path.open("r", encoding="utf-8") as handle:
                metadata = yaml.safe_load(handle)
                if not metadata or metadata.get("kind") != "Workspace":
                    findings.append(
                        ValidationFinding(
                            code="invalid_workspace_yaml",
                            severity="error",
                            path=workspace_yaml_path,
                            message="workspace.yaml must contain a valid ServiceFabric Workspace kind declaration.",
                        )
                    )
        except Exception as exc:
            findings.append(
                ValidationFinding(
                    code="invalid_workspace_yaml",
                    severity="error",
                    path=workspace_yaml_path,
                    message=f"Failed to read/parse workspace.yaml configuration: {exc}",
                )
            )

    # 3. Check layout directories are present
    directories_to_check = [
        ("applications", layout.applications),
        ("recipes", layout.recipes),
        ("libraries", layout.libraries),
        ("registry", layout.registry),
        ("bindings", layout.bindings),
        ("resources", layout.resources),
        ("runtimes", layout.runtimes),
        ("environments", layout.environments),
        ("builds", layout.builds),
        ("artifacts", layout.artifacts),
        ("installations", layout.installations),
        ("instances", layout.instances),
        ("logs", layout.logs),
        ("operations", layout.operations),
        ("locks", layout.locks),
        ("cache", layout.cache),
        ("temporary", layout.temporary),
        ("backups", layout.backups),
    ]

    for name, path in directories_to_check:
        if not path.is_dir():
            findings.append(
                ValidationFinding(
                    code="missing_layout_directory",
                    severity="error",
                    path=path,
                    message=f"Required workspace directory '{name}' is missing.",
                )
            )

    # 4. Check that registered records point to valid inside-workspace directories
    applications_registry_dir = layout.registry / "applications"
    if applications_registry_dir.is_dir():
        for record_path in applications_registry_dir.glob("*.json"):
            try:
                with record_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    app_id = data.get("application_id")
                    source_path = data.get("source_path")
                    
                    if not app_id:
                        findings.append(
                            ValidationFinding(
                                code="invalid_registry_record",
                                severity="error",
                                path=record_path,
                                message="Registry record is missing application_id.",
                            )
                        )
                        continue

                    try:
                        validate_application_id(app_id)
                    except InvalidApplicationId as exc:
                        findings.append(
                            ValidationFinding(
                                code="invalid_registry_app_id",
                                severity="error",
                                path=record_path,
                                message=f"Registry record has invalid application_id '{app_id}': {exc}",
                            )
                        )

                    if source_path:
                        resolved_source = (layout.root / source_path).resolve()
                        if not resolved_source.is_dir():
                            findings.append(
                                ValidationFinding(
                                    code="missing_source_directory",
                                    severity="error",
                                    path=resolved_source,
                                    message=f"Registered source directory for '{app_id}' does not exist: {source_path}",
                                )
                            )
                        
                        # Ensure no directory escapes workspace root
                        try:
                            resolved_root = layout.root.resolve()
                            if not resolved_source.is_relative_to(resolved_root):
                                findings.append(
                                    ValidationFinding(
                                        code="source_escapes_workspace",
                                        severity="error",
                                        path=resolved_source,
                                        message=f"Application '{app_id}' source directory escapes the workspace root.",
                                    )
                                )
                        except Exception:
                            pass
            except Exception as exc:
                findings.append(
                    ValidationFinding(
                        code="unreadable_registry_record",
                        severity="error",
                        path=record_path,
                        message=f"Failed to load registry file: {exc}",
                    )
                )

    valid = not any(finding.severity == "error" for finding in findings)
    return WorkspaceValidation(valid=valid, findings=tuple(findings))


def validate_workspace_deep(layout: WorkspaceLayout) -> WorkspaceValidation:
    """Performs deep (more expensive) checks on the workspace layout.

    Parses application specifications, checks for duplicate source registrations, detects symlinks,

    and identifies incomplete atomic writes.
    """
    structural_res = validate_workspace_structural(layout)
    findings = list(structural_res.findings)

    # 1. Reject managed symlinks
    paths_to_verify_no_symlink = [
        ("state", layout.state),
        ("registry", layout.registry),
        ("bindings", layout.bindings),
        ("resources", layout.resources),
        ("runtimes", layout.runtimes),
        ("environments", layout.environments),
        ("builds", layout.builds),
        ("artifacts", layout.artifacts),
        ("installations", layout.installations),
        ("instances", layout.instances),
        ("logs", layout.logs),
        ("operations", layout.operations),
        ("locks", layout.locks),
        ("cache", layout.cache),
        ("temporary", layout.temporary),
        ("backups", layout.backups),
    ]

    for name, path in paths_to_verify_no_symlink:
        if path.exists() and path.is_symlink():
            findings.append(
                ValidationFinding(
                    code="managed_path_is_symlink",
                    severity="error",
                    path=path,
                    message=f"Managed path '{name}' is a symbolic link, which violates security boundaries.",
                )
            )

    # Check application roots for symlinks and yaml definitions
    if layout.applications.is_dir():
        for app_root in layout.applications.iterdir():
            if app_root.is_dir():
                if app_root.is_symlink():
                    findings.append(
                        ValidationFinding(
                            code="managed_path_is_symlink",
                            severity="error",
                            path=app_root,
                            message=f"Application directory '{app_root.name}' is a symbolic link.",
                        )
                    )

                app_id = app_root.name
                try:
                    validate_application_id(app_id)
                except InvalidApplicationId:
                    # Ignore random folder names, warn about them
                    findings.append(
                        ValidationFinding(
                            code="invalid_app_directory_name",
                            severity="warning",
                            path=app_root,
                            message=f"Directory '{app_id}' under applications/ is not a valid application ID.",
                        )
                    )
                    continue

                app_yaml_path = app_root / ".servicefabric/application.yaml"
                if not app_yaml_path.is_file():
                    findings.append(
                        ValidationFinding(
                            code="missing_application_yaml",
                            severity="error",
                            path=app_yaml_path,
                            message=f"Missing application.yaml declaration for application '{app_id}'.",
                        )
                    )
                else:
                    try:
                        import yaml
                        with app_yaml_path.open("r", encoding="utf-8") as handle:
                            app_meta = yaml.safe_load(handle)
                            if not app_meta or app_meta.get("kind") != "Application":
                                findings.append(
                                    ValidationFinding(
                                        code="invalid_application_yaml",
                                        severity="error",
                                        path=app_yaml_path,
                                        message=f"application.yaml for '{app_id}' has an invalid kind or layout.",
                                    )
                                )
                    except Exception as exc:
                        findings.append(
                            ValidationFinding(
                                code="unparseable_application_yaml",
                                severity="error",
                                path=app_yaml_path,
                                message=f"Failed to parse application.yaml for '{app_id}': {exc}",
                            )
                        )

    # 2. Check for duplicate source path registration
    apps_registry_dir = layout.registry / "applications"
    if apps_registry_dir.is_dir():
        source_paths_map: dict[str, str] = {}
        for record_path in apps_registry_dir.glob("*.json"):
            try:
                with record_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    app_id = data.get("application_id")
                    source_path = data.get("source_path")
                    if app_id and source_path:
                        resolved_source = str((layout.root / source_path).resolve())
                        if resolved_source in source_paths_map:
                            findings.append(
                                ValidationFinding(
                                    code="duplicate_source_registration",
                                    severity="error",
                                    path=record_path,
                                    message=f"Source path '{source_path}' is registered to both '{app_id}' "
                                            f"and '{source_paths_map[resolved_source]}'.",
                                )
                            )
                        else:
                            source_paths_map[resolved_source] = app_id
            except Exception:
                pass

    # 3. Detect incomplete temporary atomic writes (.sf-atomic-* files)
    for search_dir in [layout.registry, layout.locks, layout.applications]:
        if search_dir.is_dir():
            for p in search_dir.rglob(".sf-atomic-*"):
                if p.is_file():
                    findings.append(
                        ValidationFinding(
                            code="incomplete_temp_write",
                            severity="warning",
                            path=p,
                            message=f"Found uncleaned temporary atomic write file: {p}",
                        )
                    )

    valid = not any(finding.severity == "error" for finding in findings)
    return WorkspaceValidation(valid=valid, findings=tuple(findings))
