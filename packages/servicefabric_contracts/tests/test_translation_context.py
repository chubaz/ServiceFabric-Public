import unittest
from pathlib import Path
from pydantic import ValidationError
from servicefabric_contracts.translation_context import TranslationContext
class ContextTests(unittest.TestCase):
 def test_context_is_explicit_and_secret_safe(self):
  path=Path(__file__).parent/"fixtures/translation_contexts/managed_static.json"; self.assertEqual(TranslationContext.model_validate_json(path.read_text()).package_version,"1.0.0")
  with self.assertRaises(ValidationError): TranslationContext.model_validate_json(path.read_text().replace('"APP_NAME"','"CLIENT_SECRET"'))
