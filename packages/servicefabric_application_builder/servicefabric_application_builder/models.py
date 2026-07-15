"""Immutable records produced by deterministic application build coordination."""

from __future__ import annotations

from dataclasses import dataclass

from servicefabric_framework_kits.plans import BuildPlan


@dataclass(frozen=True)
class FileDigest:
    """A content-addressed file in a source or output tree."""

    path: str
    content_digest: str
    size_bytes: int


@dataclass(frozen=True)
class ModuleBuildPlan:
    """A reviewed kit plan, bound to a verified source tree."""

    module_id: str
    kit_id: str
    kit_version: str
    adapter_id: str
    reviewed_plan: BuildPlan
    source_root: str
    source_digest: str
    source_files: tuple[FileDigest, ...]


@dataclass(frozen=True)
class ApplicationBuildPlan:
    """The complete deterministic build plan in assembly dependency order."""

    build_order: tuple[str, ...]
    modules: tuple[ModuleBuildPlan, ...]
    plan_digest: str


@dataclass(frozen=True)
class ModuleBuildManifest:
    """Immutable output record for one module build."""

    module_id: str
    kit_id: str
    kit_version: str
    adapter_id: str
    source_digest: str
    output_digest: str
    output_files: tuple[FileDigest, ...]


@dataclass(frozen=True)
class ApplicationBuildManifest:
    """Immutable, content-addressed multi-module build result."""

    build_order: tuple[str, ...]
    plan_digest: str
    modules: tuple[ModuleBuildManifest, ...]
    manifest_digest: str
