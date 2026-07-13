"""Architecture boundaries for the bounded AP-01A local hosting slice."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "clients/python/servicefabric_client/main.py"
HOST = ROOT / "services/application_host/servicefabric_application_host/service.py"


def imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


class Ap01aHostingBoundaryTests(unittest.TestCase):
    def test_cli_has_no_application_transport_or_implementation_import(self) -> None:
        modules = imported_modules(CLI)
        source = CLI.read_text(encoding="utf-8")
        self.assertFalse({"urllib", "urllib.request", "fastapi", "uvicorn"} & modules)
        self.assertNotIn("examples.text", source)
        self.assertNotIn("/actions/", source)
        self.assertNotIn("application.json", source)

    def test_host_is_a_bounded_adapter_not_a_second_runtime(self) -> None:
        modules = imported_modules(HOST)
        source = HOST.read_text(encoding="utf-8")
        forbidden = {
            "django",
            "flask",
            "servicefabric_runtime",
            "servicefabric_governance",
            "servicefabric_mcp_gateway",
        }
        self.assertFalse(forbidden & modules)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("0.0.0.0", source)

    def test_reviewed_actions_are_owned_only_by_host_and_application(self) -> None:
        route = "/actions/" + "count-words"
        owners = {
            path.relative_to(ROOT).as_posix()
            for root in ("clients", "examples", "packages", "services")
            for path in (ROOT / root).rglob("*.py")
            if route in path.read_text(encoding="utf-8", errors="ignore")
        }
        self.assertEqual(
            owners,
            {
                "examples/text-utility/app.py",
                "services/application_host/servicefabric_application_host/service.py",
            },
        )


if __name__ == "__main__":
    unittest.main()
