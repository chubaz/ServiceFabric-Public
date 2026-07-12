from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "packages" / "servicefabric_contracts" / "src" / "servicefabric_contracts"
MODULES = ("governance.py", "approvals.py", "durable_operations.py")
FORBIDDEN_IMPORTS = {
    "django", "flask", "fastapi", "http", "mcp", "sqlalchemy", "psycopg", "sqlite3",
    "subprocess", "requests", "httpx", "urllib", "docker", "kubernetes",
}
FORBIDDEN_FIELDS = {
    "idempotency_key", "raw_key", "policy_expression", "policy_code", "credential",
    "password", "secret", "storage_path", "filesystem_path",
}


class GovernanceContractBoundaryTests(unittest.TestCase):
    def test_contract_modules_are_framework_and_persistence_neutral(self) -> None:
        for name in MODULES:
            tree = ast.parse((CONTRACTS / name).read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertFalse(imports & FORBIDDEN_IMPORTS, f"{name}: {imports & FORBIDDEN_IMPORTS}")

    def test_contract_fields_exclude_authority_and_storage_escape_hatches(self) -> None:
        for name in MODULES:
            tree = ast.parse((CONTRACTS / name).read_text(encoding="utf-8"))
            fields = {
                target.id
                for node in ast.walk(tree)
                if isinstance(node, ast.AnnAssign)
                for target in (node.target,)
                if isinstance(target, ast.Name)
            }
            self.assertFalse(fields & FORBIDDEN_FIELDS, f"{name}: {fields & FORBIDDEN_FIELDS}")

    def test_contracts_contain_no_execution_or_persistence_implementation(self) -> None:
        forbidden_calls = {"eval", "exec", "compile", "open", "system", "popen", "run", "connect"}
        for name in MODULES:
            tree = ast.parse((CONTRACTS / name).read_text(encoding="utf-8"))
            calls = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
            self.assertFalse(calls & forbidden_calls, f"{name}: {calls & forbidden_calls}")

    def test_domain_packages_have_no_framework_or_remote_client_imports(self) -> None:
        roots = (
            ROOT / "packages/servicefabric_governance/src",
            ROOT / "packages/servicefabric_operations/src",
        )
        forbidden = FORBIDDEN_IMPORTS | {"socket", "asyncio", "django", "redis", "nats"}
        for root in roots:
            for path in root.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import): imports.update(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
                self.assertFalse(imports & forbidden, f"{path}: {imports & forbidden}")

    def test_client_does_not_import_or_manipulate_storage(self) -> None:
        client = ROOT / "clients/python/servicefabric_client/governance.py"
        source = client.read_text(encoding="utf-8")
        self.assertNotIn("servicefabric_operations", source)
        self.assertNotIn("Path(", source)
        self.assertNotIn("open(", source)

    def test_v3_does_not_add_code_execution_or_network_escape_hatches(self) -> None:
        roots = (ROOT / "packages/servicefabric_governance", ROOT / "packages/servicefabric_operations", ROOT / "services/governance_operations")
        forbidden_calls = {"eval", "exec", "compile", "system", "popen"}
        for root in roots:
            for path in root.rglob("*.py"):
                tree=ast.parse(path.read_text(encoding="utf-8"))
                calls={node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)}
                self.assertFalse(calls & forbidden_calls,f"{path}: {calls & forbidden_calls}")


if __name__ == "__main__":
    unittest.main()
