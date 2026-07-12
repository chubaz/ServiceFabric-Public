from __future__ import annotations
import ast
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "packages/servicefabric_contracts/src/servicefabric_contracts"
FORBIDDEN = {"django","rest_framework","flask","fastapi","sqlalchemy","mcp","docker","kubernetes","crewai","langchain","requests","httpx","celery"}
class InvocationContractBoundaryTests(unittest.TestCase):
    def test_invocation_contracts_are_protocol_neutral(self):
        imported=set()
        for path in SOURCE.glob("*.py"):
            tree=ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import): imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module: imported.add(node.module.split(".")[0])
        self.assertFalse(imported & FORBIDDEN)
    def test_contract_package_has_no_runtime_implementation(self):
        text="\n".join(path.read_text(encoding="utf-8") for path in SOURCE.glob("*.py"))
        for marker in ("subprocess.", "os.system", "cursor.execute", "HTTPStatus", "mcp.server"):
            self.assertNotIn(marker, text)
