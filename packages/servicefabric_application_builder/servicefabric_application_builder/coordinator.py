"""Deterministic coordination around reviewed framework-kit build plans.

This module deliberately plans and records builds only.  It never executes a
framework command; an execution owner may use the reviewed plans separately.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Mapping

from servicefabric_application_assembly import assemble_application
from servicefabric_application_model import ModuleDefinition
from servicefabric_framework_kits import FrameworkKitCatalog, KitPlanningContext, parse_kit_reference

from .models import (
    ApplicationBuildManifest,
    ApplicationBuildPlan,
    FileDigest,
    ModuleBuildManifest,
    ModuleBuildPlan,
)

if TYPE_CHECKING:
    from servicefabric_artifacts import FileArtifactStore
    from servicefabric_contracts import ApplicationArtifactManifest


class BuildCoordinationError(ValueError):
    """Raised when a proposed build cannot be safely or deterministically recorded."""


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_tree(root: Path) -> tuple[FileDigest, ...]:
    """Return sorted file digests, rejecting missing roots and symlink traversal."""
    if not root.is_dir():
        raise BuildCoordinationError(f"build tree is not a directory: {root}")
    entries: list[FileDigest] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise BuildCoordinationError(f"symlinks are not permitted in build trees: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes()
        entries.append(
            FileDigest(
                path=relative,
                content_digest="sha256:" + hashlib.sha256(content).hexdigest(),
                size_bytes=len(content),
            )
        )
    return tuple(entries)


def tree_digest(files: Iterable[FileDigest]) -> str:
    """Calculate a stable digest for a complete, normalized file listing."""
    ordered = tuple(sorted(files, key=lambda item: item.path))
    if len({item.path for item in ordered}) != len(ordered):
        raise BuildCoordinationError("duplicate paths in build tree")
    return _canonical_digest([asdict(item) for item in ordered])


class ApplicationBuildCoordinator:
    """Creates reviewed multi-module plans and immutable output manifests."""

    def __init__(self, catalog: FrameworkKitCatalog, context: KitPlanningContext):
        self._catalog = catalog
        self._context = context
        self._workspace_root = context.workspace_root.resolve()

    def plan(self, modules: Iterable[ModuleDefinition]) -> ApplicationBuildPlan:
        """Validate kit support and bind each reviewed plan to its source digest."""
        assembly = assemble_application(modules)
        planned: list[ModuleBuildPlan] = []
        for module_id in assembly.build_order:
            module = assembly.modules_by_id[module_id].module
            reference = parse_kit_reference(module.kit)
            definition, adapter = self._catalog.resolve(reference)
            if not definition.build_supported:
                raise BuildCoordinationError(
                    f"framework kit '{module.kit}' does not support builds"
                )
            self._catalog.validate_module(module)
            source_root = self._resolve_source(module.source)
            source_files = _safe_tree(source_root)
            source_digest = tree_digest(source_files)
            planned.append(
                ModuleBuildPlan(
                    module_id=module.module_id,
                    kit_id=reference.kit_id,
                    kit_version=reference.version,
                    adapter_id=definition.adapter_id,
                    reviewed_plan=adapter.build_plan(module, self._context),
                    source_root=str(source_root),
                    source_digest=source_digest,
                    source_files=source_files,
                )
            )
        plan_digest = _canonical_digest(
            {
                "build_order": assembly.build_order,
                "modules": [
                    {
                        "module_id": item.module_id,
                        "kit_id": item.kit_id,
                        "kit_version": item.kit_version,
                        "adapter_id": item.adapter_id,
                        "reviewed_plan": asdict(item.reviewed_plan),
                        "source_digest": item.source_digest,
                    }
                    for item in planned
                ],
            }
        )
        return ApplicationBuildPlan(assembly.build_order, tuple(planned), plan_digest)

    def manifest(
        self, plan: ApplicationBuildPlan, output_roots: Mapping[str, Path]
    ) -> ApplicationBuildManifest:
        """Record verified output trees without performing build execution."""
        expected = {item.module_id for item in plan.modules}
        if set(output_roots) != expected:
            raise BuildCoordinationError("output roots must match the planned module IDs exactly")
        modules: list[ModuleBuildManifest] = []
        for item in plan.modules:
            output_files = _safe_tree(Path(output_roots[item.module_id]))
            modules.append(
                ModuleBuildManifest(
                    module_id=item.module_id,
                    kit_id=item.kit_id,
                    kit_version=item.kit_version,
                    adapter_id=item.adapter_id,
                    source_digest=item.source_digest,
                    output_digest=tree_digest(output_files),
                    output_files=output_files,
                )
            )
        manifest_digest = _canonical_digest(
            {
                "build_order": plan.build_order,
                "plan_digest": plan.plan_digest,
                "modules": [asdict(item) for item in modules],
            }
        )
        return ApplicationBuildManifest(
            plan.build_order, plan.plan_digest, tuple(modules), manifest_digest
        )

    @staticmethod
    def publish_artifact(
        store: "FileArtifactStore", manifest: "ApplicationArtifactManifest", output_root: Path
    ) -> str:
        """Publish only through the existing immutable artifact-store API."""
        return store.put_artifact(manifest, output_root)

    def _resolve_source(self, source: str) -> Path:
        candidate = Path(source)
        root = candidate.resolve() if candidate.is_absolute() else (self._workspace_root / candidate).resolve()
        if root != self._workspace_root and self._workspace_root not in root.parents:
            raise BuildCoordinationError(f"module source escapes the workspace: {source}")
        return root
