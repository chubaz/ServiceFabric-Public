"""Ensure C1-00 contracts remain framework-neutral and unused by runtime services."""

from __future__ import annotations

import ast
import tomllib
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "packages" / "servicefabric_contracts"
BANNED_ROOTS = {
    "django",
    "rest_framework",
    "flask",
    "fastapi",
    "sqlalchemy",
    "chromadb",
    "mcp",
    "docker",
    "kubernetes",
    "crewai",
    "langchain",
}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


class ContractPackageBoundaryTests(unittest.TestCase):
    def test_contract_package_has_no_framework_or_runtime_imports(self) -> None:
        imports: set[str] = set()
        for path in (PACKAGE_ROOT / "src").rglob("*.py"):
            imports.update(imported_roots(path))
        self.assertFalse(imports & BANNED_ROOTS, imports & BANNED_ROOTS)

    def test_contract_metadata_declares_only_pydantic_runtime_dependency(self) -> None:
        project = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        dependencies = project["project"].get("dependencies", [])
        self.assertEqual(dependencies, ["pydantic>=2.13,<3"])

    def test_existing_service_code_does_not_import_contracts(self) -> None:
        service_roots = [
            REPOSITORY_ROOT / "2_backend_api",
            REPOSITORY_ROOT / "5_core_services",
        ]
        offenders: list[Path] = []
        for root in service_roots:
            for path in root.rglob("*.py"):
                if "servicefabric_contracts" in imported_roots(path):
                    offenders.append(path.relative_to(REPOSITORY_ROOT))
        self.assertEqual(offenders, [])
