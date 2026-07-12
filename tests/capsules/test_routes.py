from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "packages" / "servicefabric_contracts" / "src"),
    str(ROOT / "packages" / "servicefabric_capsules" / "src"),
]

from servicefabric_contracts import CapsuleRevision
from servicefabric_capsules.routes import CapsuleRouteTable


class CapsuleRouteResolutionTests(unittest.TestCase):
    def test_declared_routes_are_resolved_deterministically(self) -> None:
        revision = CapsuleRevision.model_validate_json(
            (ROOT / "portfolio" / "capsules" / "revisions" / "examples.hello-capsule-1.0.0.json").read_text(encoding="utf-8")
        )
        table = CapsuleRouteTable.from_revision(revision)
        self.assertEqual(table.declared_paths(), ("/", "/styles.css"))
        self.assertEqual(table.resolve("/").artifact_path, "index.html")
        self.assertEqual(table.resolve("/styles.css").binding_id, "hello-static")

    def test_route_traversal_is_rejected(self) -> None:
        revision = CapsuleRevision.model_validate_json(
            (ROOT / "portfolio" / "capsules" / "revisions" / "examples.hello-capsule-1.0.0.json").read_text(encoding="utf-8")
        )
        table = CapsuleRouteTable.from_revision(revision)
        with self.assertRaises(ValueError):
            table.resolve("/../index.html")
