"""Tests for deterministic framework-kit build coordination."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_application_builder import (
    ApplicationBuildCoordinator,
    BuildCoordinationError,
)
from servicefabric_application_model import LifecycleConfig, ModuleDefinition
from servicefabric_framework_kits import KitPlanningContext, get_default_catalog


def module(module_id: str, source: str, *, start_after: tuple[str, ...] = ()) -> ModuleDefinition:
    return ModuleDefinition(
        module_id=module_id,
        version="1.0.0",
        primitive="service",
        kit="fastapi-service @ServiceFabric/portfolio/applications/revisions/fastapi-service-1.0.0.json",
        source=source,
        lifecycle=LifecycleConfig(start_after=start_after),
    )


class ApplicationBuildCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.context = KitPlanningContext(
            workspace_root=self.root,
            state_root=self.root / ".servicefabric",
            artifacts_dir=self.root / ".servicefabric" / "artifacts",
            logs_dir=self.root / ".servicefabric" / "logs",
        )
        self.coordinator = ApplicationBuildCoordinator(get_default_catalog(), self.context)
        for name, content in (("api", "from fastapi import FastAPI\n"), ("web", "print('web')\n")):
            directory = self.root / name
            directory.mkdir()
            (directory / "app.py").write_text(content, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_plan_uses_assembly_order_and_is_stable(self) -> None:
        modules = (module("web", "web", start_after=("api",)), module("api", "api"))

        first = self.coordinator.plan(modules)
        second = self.coordinator.plan(reversed(modules))

        self.assertEqual(first.build_order, ("api", "web"))
        self.assertEqual(first, second)
        self.assertEqual(first.modules[0].reviewed_plan.adapter_id, "python-package")
        self.assertTrue(first.modules[0].source_digest.startswith("sha256:"))

    def test_manifest_is_stable_and_tracks_output_changes(self) -> None:
        plan = self.coordinator.plan((module("api", "api"),))
        output = self.root / "output"
        output.mkdir()
        (output / "package.txt").write_text("first\n", encoding="utf-8")

        first = self.coordinator.manifest(plan, {"api": output})
        second = self.coordinator.manifest(plan, {"api": output})
        (output / "package.txt").write_text("second\n", encoding="utf-8")
        changed = self.coordinator.manifest(plan, {"api": output})

        self.assertEqual(first, second)
        self.assertNotEqual(first.manifest_digest, changed.manifest_digest)
        self.assertNotEqual(first.modules[0].output_digest, changed.modules[0].output_digest)

    def test_rejects_wrong_output_set_and_workspace_escape(self) -> None:
        plan = self.coordinator.plan((module("api", "api"),))
        with self.assertRaisesRegex(BuildCoordinationError, "match"):
            self.coordinator.manifest(plan, {})
        with self.assertRaisesRegex(BuildCoordinationError, "escapes"):
            self.coordinator.plan((module("api", "../outside"),))

    def test_publish_delegates_to_the_artifact_store(self) -> None:
        class Store:
            def __init__(self) -> None:
                self.called_with = None

            def put_artifact(self, manifest, root):
                self.called_with = (manifest, root)
                return "sha256:" + "a" * 64

        store = Store()
        output = self.root / "output"
        output.mkdir()
        result = ApplicationBuildCoordinator.publish_artifact(store, object(), output)

        self.assertEqual(result, "sha256:" + "a" * 64)
        self.assertEqual(store.called_with, (store.called_with[0], output))
