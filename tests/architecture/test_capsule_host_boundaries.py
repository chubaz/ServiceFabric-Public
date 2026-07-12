from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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
    "requests",
    "httpx",
    "subprocess",
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


class CapsuleHostBoundaryTests(unittest.TestCase):
    def test_capsule_package_remains_framework_neutral(self) -> None:
        imports: set[str] = set()
        for path in (ROOT / "packages" / "servicefabric_capsules" / "src").rglob("*.py"):
            imports.update(imported_roots(path))
        self.assertFalse(imports & BANNED_ROOTS, imports & BANNED_ROOTS)

    def test_runtime_services_do_not_import_capsules_yet(self) -> None:
        offenders: list[Path] = []
        for root in [ROOT / "2_backend_api", ROOT / "5_core_services", ROOT / "packages" / "servicefabric_runtime", ROOT / "clients" / "python"]:
            for path in root.rglob("*.py"):
                if "servicefabric_capsules" in imported_roots(path):
                    offenders.append(path.relative_to(ROOT))
        self.assertEqual(offenders, [])

