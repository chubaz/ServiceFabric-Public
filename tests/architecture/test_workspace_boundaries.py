"""Architecture boundaries for ServiceFabric Application Workspaces."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "clients/python/servicefabric_client/main.py"
HOST = ROOT / "services/application_host/servicefabric_application_host/service.py"
WORKSPACE_PKG = ROOT / "packages/servicefabric_workspace/servicefabric_workspace"


def imported_modules(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    try:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                yield from (alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                yield node.module
    except Exception:
        pass


class WorkspaceArchitectureBoundaryTests(unittest.TestCase):
    def test_cli_has_no_raw_workspace_path_helpers(self) -> None:
        cli_source = CLI.read_text(encoding="utf-8")
        # Ensure raw functions are removed/not present
        self.assertNotIn("def workspace_path(", cli_source)
        self.assertNotIn("def init_workspace(", cli_source)

    def test_workspace_package_has_no_upward_dependencies(self) -> None:
        # servicefabric_workspace must never import the client, host, builder, or Django
        forbidden_imports = {
            "servicefabric_client",
            "servicefabric_application_host",
            "servicefabric_builder",
            "django",
            "flask",
        }
        for path in WORKSPACE_PKG.rglob("*.py"):
            imports = set(imported_modules(path))
            escapes = forbidden_imports & imports
            self.assertFalse(
                escapes,
                f"Workspace package file '{path.relative_to(ROOT)}' illegally imports upward modules: {escapes}",
            )

    def test_components_do_not_read_workspace_env_variables_directly(self) -> None:
        # Only the workspace resolver or main composition root should inspect env variables.
        # Other services must rely on the resolved paths passed to them.
        env_vars = ["SERVICEFABRIC_WORKSPACE", "SERVICEFABRIC_HOME"]
        
        # Scan directories that should not reference env vars
        scanned_roots = [
            ROOT / "services/application_host",
            ROOT / "packages/servicefabric_builder",
            ROOT / "packages/servicefabric_artifacts",
            ROOT / "packages/servicefabric_governance",
        ]
        
        for root in scanned_roots:
            for path in root.rglob("*.py"):
                # Exclude tests
                if "tests" in path.parts:
                    continue
                content = path.read_text(encoding="utf-8", errors="ignore")
                for var in env_vars:
                    self.assertNotIn(
                        f'"{var}"',
                        content,
                        f"Direct env var access of {var} found in service file '{path.relative_to(ROOT)}'",
                    )
                    self.assertNotIn(
                        f"'{var}'",
                        content,
                        f"Direct env var access of {var} found in service file '{path.relative_to(ROOT)}'",
                    )


if __name__ == "__main__":
    unittest.main()
