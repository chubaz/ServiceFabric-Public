"""Workspace path resolution logic."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from servicefabric_workspace.errors import InvalidWorkspaceConfiguration
from servicefabric_workspace.models import WorkspaceContext, WorkspaceLayout


def resolve_workspace(
    explicit_workspace: Path | None = None,
    explicit_state: Path | None = None,
) -> WorkspaceContext:
    """Resolves the WorkspaceLayout and returns a WorkspaceContext based on explicit paths,

    environment variables, or defaults.

    Args:
        explicit_workspace: An optional explicitly provided workspace root path.
        explicit_state: An optional explicitly provided state directory path.

    Returns:
        A WorkspaceContext detailing the layout, mode, and resolution source.

    Raises:
        InvalidWorkspaceConfiguration: If root and state directories are incompatible.
    """
    env_workspace = os.environ.get("SERVICEFABRIC_WORKSPACE")
    env_home = os.environ.get("SERVICEFABRIC_HOME")

    # 1. Explicitly provided paths
    if explicit_workspace is not None:
        root = Path(explicit_workspace)
        state = Path(explicit_state) if explicit_state is not None else root / ".servicefabric"
        layout = WorkspaceLayout.from_root(root, state)
        context = WorkspaceContext(
            layout=layout,
            mode="external",
            resolution_source="explicit",
        )
        _validate_roots_relationship(context)
        return context

    # 2. Environment variables: both are set
    if env_workspace and env_home:
        root = Path(env_workspace)
        state = Path(env_home)
        layout = WorkspaceLayout.from_root(root, state)
        context = WorkspaceContext(
            layout=layout,
            mode="external",
            resolution_source="environment",
        )
        _validate_roots_relationship(context)
        return context

    # 3. Environment variables: only workspace is set
    if env_workspace:
        root = Path(env_workspace)
        state = root / ".servicefabric"
        layout = WorkspaceLayout.from_root(root, state)
        context = WorkspaceContext(
            layout=layout,
            mode="external",
            resolution_source="environment",
        )
        _validate_roots_relationship(context)
        return context

    # 4. Environment variables: only legacy state/home is set
    if env_home:
        state = Path(env_home)
        workspace_file = state / "workspace.yaml"
        # If workspace.yaml does not exist under HOME, resolve as legacy AP-01A mode
        if not workspace_file.is_file():
            # In legacy mode, root is mapped directly to state (no source workspace exists)
            layout = WorkspaceLayout.from_root(state, state)
            return WorkspaceContext(
                layout=layout,
                mode="legacy-state-only",
                resolution_source="legacy-home",
            )
        else:
            # If workspace.yaml exists in env_home, it's actually configured
            # as an external workspace with the root being the parent of env_home.
            root = state.parent
            layout = WorkspaceLayout.from_root(root, state)
            context = WorkspaceContext(
                layout=layout,
                mode="external",
                resolution_source="environment",
            )
            _validate_roots_relationship(context)
            return context

    # 5. Default: Current directory
    root = Path.cwd()
    state = root / ".servicefabric"
    layout = WorkspaceLayout.from_root(root, state)
    context = WorkspaceContext(
        layout=layout,
        mode="external",
        resolution_source="current-directory",
    )
    _validate_roots_relationship(context)
    return context


def _validate_roots_relationship(context: WorkspaceContext) -> None:
    """Rejects unsafe or contradictory relationships between root and state."""
    if context.mode == "legacy-state-only":
        return

    try:
        resolved_root = context.layout.root.resolve()
        resolved_state = context.layout.state.resolve()
    except Exception:
        # If directories don't exist yet, we use strict=False-like resolution
        resolved_root = context.layout.root.absolute()
        resolved_state = context.layout.state.absolute()

    # Reject if workspace root is nested inside the platform state folder
    if resolved_root == resolved_state or resolved_root.is_relative_to(resolved_state):
        raise InvalidWorkspaceConfiguration(
            f"Unsafe roots configuration: workspace root '{context.layout.root}' "
            f"cannot be nested inside or equal to the state directory '{context.layout.state}'"
        )
