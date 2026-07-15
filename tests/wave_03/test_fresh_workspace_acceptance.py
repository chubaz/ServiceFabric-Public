"""Executable acceptance specification for the Wave-3 integration journey.

This lane owns the stable, framework-spanning expectations.  The generator,
builder, and CLI lanes supply the implementation that the integration gate
executes against this specification.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "wave_03" / "fresh_workspace_journey.json"


class FreshWorkspaceAcceptanceSpecificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specification = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_journey_is_the_required_fresh_workspace_lifecycle(self) -> None:
        self.assertEqual(
            [step["command"] for step in self.specification["journey"]],
            [
                "workspace init",
                "apps create",
                "apps modules",
                "apps validate",
                "dev prepare",
                "dev start",
                "dev status",
                "dev restart",
                "apps build",
                "dev stop",
            ],
        )

    def test_generation_covers_ordinary_supported_framework_source(self) -> None:
        modules = self.specification["application"]["modules"]
        self.assertEqual(
            [(module["id"], module["kit"]) for module in modules],
            [
                ("api", "fastapi-service"),
                ("web", "react-web"),
                ("domain", "python-library"),
            ],
        )
        for module in modules:
            self.assertTrue(module["ordinary_source"].strip(), module["id"])
            self.assertNotIn("servicefabric_runtime", module["ordinary_source"])

    def test_each_lifecycle_transition_has_an_observable_assertion(self) -> None:
        assertions = {
            step["command"]: set(step["assertions"])
            for step in self.specification["journey"]
        }
        self.assertIn("prepared_lifecycle_state", assertions["dev prepare"])
        self.assertIn("running_lifecycle_state", assertions["dev start"])
        self.assertIn("preserved_module_state", assertions["dev status"])
        self.assertIn("preserved_module_state", assertions["dev restart"])
        self.assertIn("stopped_lifecycle_state", assertions["dev stop"])

    def test_collision_rollback_and_cleanup_are_non_destructive(self) -> None:
        safety = self.specification["safety"]
        self.assertEqual(
            safety["collision"],
            ["reject_existing_application", "leave_existing_files_unchanged"],
        )
        self.assertEqual(
            safety["rollback"],
            ["remove_partial_generated_files", "leave_no_application_registry_record"],
        )
        self.assertEqual(
            safety["cleanup"],
            [
                "remove_temporary_runtime_files",
                "preserve_generated_source",
                "preserve_build_manifest",
            ],
        )

    def test_build_manifest_is_immutable_and_digest_addressable(self) -> None:
        self.assertEqual(
            self.specification["build_manifest"],
            ["application_id", "source_digest", "output_digest", "modules", "immutable"],
        )


if __name__ == "__main__":
    unittest.main()
