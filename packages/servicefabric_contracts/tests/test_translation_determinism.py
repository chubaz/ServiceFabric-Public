import unittest
from pathlib import Path
from servicefabric_contracts.legacy_translation import translate_legacy_manifest
from servicefabric_contracts.translation_context import TranslationContext
ROOT=Path(__file__).resolve().parents[3]
class DeterminismTests(unittest.TestCase):
 def test_same_inputs_produce_same_json(self):
  source=(ROOT/"3_service_templates/vite_base/fabric-manifest.json").read_bytes(); context=TranslationContext.model_validate_json((Path(__file__).parent/"fixtures/translation_contexts/managed_static.json").read_text()); self.assertEqual(translate_legacy_manifest(source,context).model_dump_json(),translate_legacy_manifest(source,context).model_dump_json())
