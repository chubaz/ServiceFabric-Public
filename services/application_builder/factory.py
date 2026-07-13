"""Explicit constructors for the local application-builder service boundary."""

from __future__ import annotations

from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio

from .service import ApplicationBuilderService


def create_application_builder_service(
    *, portfolio_root: Path, artifact_store_root: Path
) -> ApplicationBuilderService:
    """Construct the bounded builder service from reviewed local roots."""
    return ApplicationBuilderService(
        ApplicationPortfolio(portfolio_root), FileArtifactStore(artifact_store_root)
    )
