"""Architecture tests enforcing boundaries against deprecated legacy generation paths."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

# Explicit, strictly restricted allowlist of files permitted to reference legacy paths
ALLOWED_LEGACY_REFERENCES = {
    "2_backend_api/service_fabric/core/service_generator.py",
    "2_backend_api/service_fabric/myproject/settings.py",
    "tests/architecture/test_legacy_application_paths.py",
}


class LegacyApplicationPathsBoundaryTests(unittest.TestCase):
    def test_new_code_does_not_depend_on_legacy_application_paths(self) -> None:
        legacy_paths = ["3_service_templates", "4_generated_services", "6_service_catalog"]
        
        # We will scan the new workspace package and the CLI client
        scanned_directories = [
            ROOT / "packages/servicefabric_workspace",
            ROOT / "clients/python/servicefabric_client",
        ]

        for root in scanned_directories:
            for path in root.rglob("*.py"):
                relative_path = path.relative_to(ROOT).as_posix()
                if relative_path in ALLOWED_LEGACY_REFERENCES:
                    continue
                
                content = path.read_text(encoding="utf-8", errors="ignore")
                for legacy in legacy_paths:
                    self.assertNotIn(
                        legacy,
                        content,
                        f"Legacy path reference '{legacy}' illegally found in new workspace/client file: {relative_path}",
                    )


if __name__ == "__main__":
    unittest.main()
