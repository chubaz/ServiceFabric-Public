"""Domain exceptions for ServiceFabric Framework Kits."""

from __future__ import annotations


class KitError(RuntimeError):
    """Base exception for all framework kit errors."""
    pass


class InvalidKitReference(KitError):
    """Raised when a framework kit reference string is malformed or invalid."""
    pass


class DuplicateKitRegistration(KitError):
    """Raised when attempting to register a duplicate kit ID and version."""
    pass


class KitNotFound(KitError):
    """Raised when a referenced framework kit cannot be found in the catalog."""
    pass


class PrimitiveMismatch(KitError):
    """Raised when a framework kit is assigned to a module using an incompatible primitive."""
    pass
