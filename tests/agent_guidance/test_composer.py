"""Tests for deterministic generated root and module guidance."""

from __future__ import annotations

import unittest

from servicefabric_agent_guidance import (
    GuidanceFragment,
    InvalidGuidancePath,
    UnknownGuidanceKit,
    compose_guidance,
)


class GuidanceComposerTests(unittest.TestCase):
    def test_composes_deterministic_root_and_reviewed_module_fragments(self) -> None:
        bundle = compose_guidance(
            {
                "web": "react-web @reviewed/react-web-1.json",
                "api": "fastapi-service @reviewed/fastapi-1.json",
            }
        )

        self.assertEqual(
            bundle.paths(),
            ("AGENTS.md", "modules/api/AGENTS.md", "modules/web/AGENTS.md"),
        )
        self.assertIn("Application Guidance", bundle.files["AGENTS.md"])
        self.assertIn("ordinary FastAPI code", bundle.files["modules/api/AGENTS.md"])
        self.assertIn("ordinary React source", bundle.files["modules/web/AGENTS.md"])
        self.assertTrue(all(value.endswith("\n") for value in bundle.files.values()))

    def test_rejects_unknown_kit_instead_of_emitting_unreviewed_guidance(self) -> None:
        with self.assertRaises(UnknownGuidanceKit):
            compose_guidance({"api": "unreviewed-kit@1.0.0"})

    def test_rejects_unsafe_output_paths(self) -> None:
        with self.assertRaises(InvalidGuidancePath):
            GuidanceFragment("unsafe", "../AGENTS.md", "not allowed")

    def test_supports_python_module_kits(self) -> None:
        bundle = compose_guidance({"tasks": "python-worker@1.0.0"})
        self.assertIn("ordinary Python code", bundle.files["modules/tasks/AGENTS.md"])


if __name__ == "__main__":
    unittest.main()
