import unittest
from pathlib import Path
from servicefabric_contracts.legacy_translation import translate_legacy_manifest
from servicefabric_contracts.translation_context import TranslationContext
ROOT=Path(__file__).resolve().parents[3]
class TranslationTests(unittest.TestCase):
 def context(self,name): return TranslationContext.model_validate_json((Path(__file__).parent/f"fixtures/translation_contexts/{name}.json").read_text())
 def test_static_translates_and_flask_and_composite_do_not(self):
  vite=(ROOT/"3_service_templates/vite_base/fabric-manifest.json").read_bytes(); result=translate_legacy_manifest(vite,self.context("managed_static")); self.assertIsNotNone(result.canonical_resource)
  flask=(ROOT/"3_service_templates/flask_base/fabric-manifest.json").read_bytes(); report=translate_legacy_manifest(flask,self.context("legacy_shared_host")); self.assertIsNone(report.canonical_resource); self.assertIn("LEGACY_SHARED_HOST_REQUIRES_ADAPTER",{d.code for d in report.diagnostics})
  quant=(ROOT/"3_service_templates/quant_vite_base/fabric-manifest.json").read_bytes(); report=translate_legacy_manifest(quant,self.context("composite_review")); self.assertEqual(report.status,"requires_split")
