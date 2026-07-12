import unittest
from servicefabric_contracts.legacy_manifest import DuplicateJsonKey, parse_legacy_manifest
class LegacyManifestTests(unittest.TestCase):
 def test_duplicate_keys_and_size_are_rejected(self):
  with self.assertRaises(DuplicateJsonKey): parse_legacy_manifest(b'{"app_name":"a","app_name":"b"}')
  with self.assertRaises(ValueError): parse_legacy_manifest(b" "*(128*1024+1))
