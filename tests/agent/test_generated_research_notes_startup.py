"""Regression coverage for generated Research Notes development startup."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from servicefabric_client.main import dispatch


class GeneratedResearchNotesStartupTests(unittest.TestCase):
    def test_freshly_generated_application_starts_executable_modules_and_is_healthy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="servicefabric-generated-notes-") as temporary:
            workspace = Path(temporary) / "workspace"

            def call(*arguments: str) -> dict[str, object]:
                with patch.dict(os.environ, {"SERVICEFABRIC_WORKSPACE": str(workspace)}, clear=False):
                    os.environ.pop("SERVICEFABRIC_HOME", None)
                    code, _, value = dispatch(list(arguments))
                self.assertEqual(code, 0)
                return value

            call("workspace", "init", str(workspace))
            call("apps", "create", "research-notes", "--template", "modular-web-app")
            call("apps", "dev", "prepare", "research-notes")
            try:
                started = call("apps", "dev", "start", "research-notes")["start"]
                self.assertEqual(started["state"], "running")  # type: ignore[index]
                modules = started["modules"]  # type: ignore[index]
                self.assertEqual(modules["notes-api"]["health"], "healthy")  # type: ignore[index]
                self.assertEqual(modules["notes-web"]["health"], "healthy")  # type: ignore[index]
            finally:
                call("apps", "dev", "stop", "research-notes")


if __name__ == "__main__":
    unittest.main()
