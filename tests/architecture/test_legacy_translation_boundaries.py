import ast, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SRC=ROOT/"packages/servicefabric_contracts/src/servicefabric_contracts"
FORBIDDEN={"django","rest_framework","flask","fastapi","sqlalchemy","mcp","docker","kubernetes","jinja2","subprocess","requests","httpx","urllib"}
class LegacyTranslationBoundaryTests(unittest.TestCase):
 def test_translation_imports_are_offline_and_framework_neutral(self):
  imported=set()
  for path in SRC.glob("*translation*.py"):
   for node in ast.walk(ast.parse(path.read_text())):
    if isinstance(node,ast.Import): imported.update(a.name.split('.')[0] for a in node.names)
    elif isinstance(node,ast.ImportFrom) and node.module: imported.add(node.module.split('.')[0])
  self.assertFalse(imported & FORBIDDEN)
 def test_runtime_and_generator_do_not_import_translator(self):
  for root in (ROOT/"2_backend_api",ROOT/"5_core_services"):
   for path in root.rglob("*.py"): self.assertNotIn("legacy_translation",path.read_text(errors="ignore"))
 def test_compose_does_not_invoke_translator(self):
  for path in ROOT.glob("docker-compose*.yml"): self.assertNotIn("translate_legacy_manifest",path.read_text())
