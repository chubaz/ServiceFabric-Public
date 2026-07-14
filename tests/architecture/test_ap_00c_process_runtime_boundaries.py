"""Architecture regressions for the frozen AP-00C process runtime surface."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROCESS_RUNTIME = ROOT / "packages/servicefabric_process_runtime/servicefabric_process_runtime"

FORBIDDEN_IMPORT_ROOTS = {
    "django",
    "flask",
    "fastapi",
    "uvicorn",
    "requests",
    "httpx",
    "docker",
    "kubernetes",
    "servicefabric_application_assembly",
    "servicefabric_blueprints",
    "servicefabric_resource_bindings",
}
FORBIDDEN_DYNAMIC_EXECUTION = {"eval", "exec", "compile"}


def parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


class Ap00cProcessRuntimeBoundaryTests(unittest.TestCase):
    def test_process_runtime_remains_framework_and_wave_lane_neutral(self) -> None:
        offenders: list[str] = []
        for path in PROCESS_RUNTIME.rglob("*.py"):
            for node in ast.walk(parse(path)):
                roots: set[str]
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".", 1)[0] for alias in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module:
                    roots = {node.module.split(".", 1)[0]}
                else:
                    continue
                for root in roots & FORBIDDEN_IMPORT_ROOTS:
                    offenders.append(f"{path.relative_to(ROOT)}:{root}")
        self.assertEqual(offenders, [])

    def test_process_runtime_contains_no_dynamic_code_execution_escape_hatches(self) -> None:
        offenders: list[str] = []
        for path in PROCESS_RUNTIME.rglob("*.py"):
            for node in ast.walk(parse(path)):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in FORBIDDEN_DYNAMIC_EXECUTION:
                        offenders.append(f"{path.relative_to(ROOT)}:{node.func.id}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in {"system", "popen"}:
                        offenders.append(f"{path.relative_to(ROOT)}:{node.func.attr}")
        self.assertEqual(offenders, [])

    def test_runtime_status_model_keeps_identity_separate_from_health_and_resources(self) -> None:
        models = parse(PROCESS_RUNTIME / "models.py")
        class_fields: dict[str, set[str]] = {}
        for node in ast.walk(models):
            if isinstance(node, ast.ClassDef):
                fields = {
                    statement.target.id
                    for statement in node.body
                    if isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                }
                class_fields[node.name] = fields

        self.assertIn("identity", class_fields["ProcessStatus"])
        self.assertIn("health", class_fields["ProcessStatus"])
        self.assertNotIn("current_memory_bytes", class_fields["ProcessStatus"])
        self.assertNotIn("recent_cpu_percent", class_fields["ProcessStatus"])
        self.assertIn("current_memory_bytes", class_fields["ProcessResourceSnapshot"])
        self.assertNotIn("health", class_fields["ProcessResourceSnapshot"])


if __name__ == "__main__":
    unittest.main()
