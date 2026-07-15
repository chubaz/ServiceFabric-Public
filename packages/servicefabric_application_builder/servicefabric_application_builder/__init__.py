"""Deterministic application build coordination and compatibility factory."""

from __future__ import annotations

from pathlib import Path

from .coordinator import ApplicationBuildCoordinator, BuildCoordinationError, tree_digest
from .models import (
    ApplicationBuildManifest,
    ApplicationBuildPlan,
    FileDigest,
    ModuleBuildManifest,
    ModuleBuildPlan,
)


def create_application_builder_service(*, portfolio_root: Path, artifact_store_root: Path):
    """Construct the existing bounded application-build service for local callers.

    The factory is intentionally a thin compatibility projection; build business
    logic remains with the existing canonical service boundary.
    """
    from servicefabric_artifacts import FileArtifactStore
    from servicefabric_builder import ApplicationPortfolio
    from services.application_builder import ApplicationBuilderService

    return ApplicationBuilderService(
        ApplicationPortfolio(portfolio_root), FileArtifactStore(artifact_store_root)
    )


__all__ = [
    "ApplicationBuildCoordinator",
    "ApplicationBuildManifest",
    "ApplicationBuildPlan",
    "BuildCoordinationError",
    "FileDigest",
    "ModuleBuildManifest",
    "ModuleBuildPlan",
    "create_application_builder_service",
    "tree_digest",
]
