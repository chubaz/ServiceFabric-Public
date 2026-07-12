"""C1-01 tool lifecycle contracts must remain declarations, never runtime code."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_SOURCE = REPOSITORY_ROOT / "packages" / "servicefabric_contracts" / "src"
BANNED_IMPORTS = {
    "django", "rest_framework", "flask", "fastapi", "sqlalchemy", "mcp", "docker",
    "kubernetes", "crewai", "langchain", "chromadb", "openai", "anthropic", "boto3",
    "google", "azure", "requests", "httpx", "api", "app", "myproject",
}
BANNED_BUILTINS = {"eval", "exec", "compile"}
BANNED_PROCESS_CALLS = {"system", "popen", "run", "call", "check_call", "check_output"}


def parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class ToolContractBoundaryTests(unittest.TestCase):
    def test_tool_contracts_import_no_framework_runtime_or_provider_sdk(self) -> None:
        offenders: list[str] = []
        for path in CONTRACT_SOURCE.rglob("*.py"):
            for node in ast.walk(parse(path)):
                if isinstance(node, ast.Import):
                    roots = [alias.name.split(".", 1)[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    roots = [node.module.split(".", 1)[0]]
                else:
                    continue
                for root in roots:
                    if root in BANNED_IMPORTS:
                        offenders.append(f"{path.relative_to(REPOSITORY_ROOT)}:{root}")
        self.assertEqual(offenders, [])

    def test_contract_package_contains_no_shell_sql_or_process_execution(self) -> None:
        offenders: list[str] = []
        for path in CONTRACT_SOURCE.rglob("*.py"):
            for node in ast.walk(parse(path)):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id in BANNED_BUILTINS:
                    offenders.append(f"{path.relative_to(REPOSITORY_ROOT)}:{node.func.id}")
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id in {"os", "subprocess"} and node.func.attr in BANNED_PROCESS_CALLS:
                        offenders.append(f"{path.relative_to(REPOSITORY_ROOT)}:{node.func.value.id}.{node.func.attr}")
        self.assertEqual(offenders, [])

    def test_production_services_still_do_not_import_contract_package(self) -> None:
        offenders: list[Path] = []
        for root_name in ("2_backend_api", "5_core_services"):
            for path in (REPOSITORY_ROOT / root_name).rglob("*.py"):
                for node in ast.walk(parse(path)):
                    if isinstance(node, ast.Import) and any(alias.name.startswith("servicefabric_contracts") for alias in node.names):
                        offenders.append(path.relative_to(REPOSITORY_ROOT))
                    if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("servicefabric_contracts"):
                        offenders.append(path.relative_to(REPOSITORY_ROOT))
        self.assertEqual(offenders, [])
