"""Explicit constructors for the bounded local capsule-host service."""

from __future__ import annotations

from pathlib import Path

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from servicefabric_capsules import CapsuleHostService, CapsulePortfolio


def create_capsule_host_service(
    *,
    capsule_portfolio_root: Path,
    application_portfolio_root: Path,
    artifact_store_root: Path,
) -> CapsuleHostService:
    """Construct a capsule host using only reviewed portfolios and artifacts."""
    return CapsuleHostService(
        CapsulePortfolio(capsule_portfolio_root),
        ApplicationPortfolio(application_portfolio_root),
        FileArtifactStore(artifact_store_root),
    )
