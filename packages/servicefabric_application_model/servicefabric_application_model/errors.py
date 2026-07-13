"""Domain exceptions for the ServiceFabric Application Model."""

from __future__ import annotations


class ModelError(RuntimeError):
    """Base exception for all application model errors."""
    pass


class InvalidModuleDefinition(ModelError):
    """Raised when a module manifest or schema validation fails."""
    pass


class InvalidPrimitive(ModelError):
    """Raised when an invalid primitive kind is referenced."""
    pass


class ValidationError(ModelError):
    """Raised when application graph or modular validation fails."""
    pass


class DependencyError(ModelError):
    """Raised when there are missing dependencies or cycles in the application graph."""
    pass
