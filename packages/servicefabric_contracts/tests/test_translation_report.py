import unittest
from pydantic import ValidationError
from servicefabric_contracts.translation_report import LegacyManifestTranslationReport
class ReportTests(unittest.TestCase):
 def test_translated_requires_resource(self):
  with self.assertRaises(ValidationError): LegacyManifestTranslationReport(apiVersion="servicefabric.ai/v1alpha1",kind="LegacyManifestTranslationReport",status="translated",source={"kind":"unknown","reference":"x"},source_digest="sha256:"+"a"*64,profile="assessment_only")
