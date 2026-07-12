import ast
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class BuilderBoundaryTests(unittest.TestCase):
    def imports(self, root):
        result = set()
        for path in root.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    result.update(item.name.split(".")[0] for item in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    result.add(node.module.split(".")[0])
        return result

    def test_contracts_do_not_import_builder_implementation(self):
        imports = self.imports(ROOT / "packages/servicefabric_contracts/src")
        self.assertFalse(imports & {"servicefabric_builder", "servicefabric_artifacts", "docker", "subprocess"})

    def test_builder_has_no_execution_or_network_clients(self):
        imports = self.imports(ROOT / "packages/servicefabric_builder")
        self.assertFalse(imports & {"subprocess", "socket", "requests", "httpx", "docker"})
        for path in (ROOT / "packages/servicefabric_builder").rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("shell=True", source)
            self.assertNotIn("os.system", source)

    def test_client_does_not_import_builder_adapters(self):
        imports = self.imports(ROOT / "clients/python")
        self.assertFalse(imports & {"servicefabric_builder", "servicefabric_artifacts"})

    def test_prohibited_runtime_areas_are_unchanged(self):
        result = subprocess.run(
            ["git", "diff", "--name-only", "main...HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        changed = set(result.stdout.splitlines())
        forbidden = {"docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"}
        self.assertFalse(changed & forbidden)
        self.assertFalse(any("/migrations/" in path or path.startswith(("3_service_templates/", "6_service_catalog/")) for path in changed))
