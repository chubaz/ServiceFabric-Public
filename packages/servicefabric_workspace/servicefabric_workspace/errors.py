"""Workspace domain exceptions."""

from __future__ import annotations


class WorkspaceError(RuntimeError):
    """Base exception for all workspace-related errors."""
    pass


class WorkspaceNotInitialized(WorkspaceError):
    """Raised when an operation requires an initialized workspace but none is found."""
    pass


class InvalidWorkspaceConfiguration(WorkspaceError):
    """Raised when workspace configuration metadata is invalid or incompatible."""
    pass


class InvalidApplicationId(WorkspaceError):
    """Raised when an application ID fails validation."""
    pass


class ApplicationAlreadyExists(WorkspaceError):
    """Raised when attempting to create an application that already exists."""
    pass


class ApplicationNotFound(WorkspaceError):
    """Raised when an application is not registered or found on disk."""
    pass


class PathEscapesWorkspace(WorkspaceError):
    """Raised when a resolved path is outside the allowed workspace or home root."""
    pass


class ManagedPathIsSymlink(WorkspaceError):
    """Raised when a managed workspace directory or file is a symbolic link."""
    pass


class RegistryConflict(WorkspaceError):
    """Raised when registry records are inconsistent or conflicting."""
    pass
