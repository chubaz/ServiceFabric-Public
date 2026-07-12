import unittest
from pydantic import ValidationError
from servicefabric_contracts.legacy_manifest import LegacyManifest
class SecurityTests(unittest.TestCase):
 def test_secret_like_core_service_key_is_rejected(self):
  with self.assertRaises(ValidationError): LegacyManifest(app_name="x",app_slug="x",template="x",description="x",core_services={"api_token":"redacted"},rules={})
