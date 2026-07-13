"""ServiceFabric Workspace and Application Lifecycle Layout Library."""

from __future__ import annotations

from servicefabric_workspace.errors import (
    ApplicationAlreadyExists,
    ApplicationNotFound,
    InvalidApplicationId,
    InvalidWorkspaceConfiguration,
    ManagedPathIsSymlink,
    PathEscapesWorkspace,
    RegistryConflict,
    WorkspaceError,
    WorkspaceNotInitialized,
)
from servicefabric_workspace.identifiers import validate_application_id
from servicefabric_workspace.models import (
    ApplicationCreateRequest,
    ApplicationLayout,
    WorkspaceContext,
    WorkspaceLayout,
    WorkspaceStatus,
    WorkspaceValidation,
    ApplicationHostPaths,
    ApplicationRecord,
)
from servicefabric_workspace.resolution import resolve_workspace
from servicefabric_workspace.service import WorkspaceService

__all__ = [
    "ApplicationCreateRequest",
    "ApplicationLayout",
    "WorkspaceContext",
    "WorkspaceLayout",
    "WorkspaceStatus",
    "WorkspaceValidation",
    "ApplicationHostPaths",
    "ApplicationRecord",
    "resolve_workspace",
    "WorkspaceService",
    "validate_application_id",
    "WorkspaceError",
    "WorkspaceNotInitialized",
    "InvalidWorkspaceConfiguration",
    "InvalidApplicationId",
    "ApplicationAlreadyExists",
    "ApplicationNotFound",
    "PathEscapesWorkspace",
    "ManagedPathIsSymlink",
    "RegistryConflict",
]
