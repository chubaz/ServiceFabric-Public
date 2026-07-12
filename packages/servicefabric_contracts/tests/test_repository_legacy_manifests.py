import unittest
from pathlib import Path
from servicefabric_contracts.legacy_manifest import parse_legacy_manifest
ROOT=Path(__file__).resolve().parents[3]
class RepositoryManifestTests(unittest.TestCase):
 def test_all_seven_repository_manifests_parse(self):
  paths=sorted((ROOT/"3_service_templates").glob("*/fabric-manifest.json"))+sorted((ROOT/"6_service_catalog").glob("*/fabric-manifest.json")); self.assertEqual(len(paths),7)
  for path in paths: parse_legacy_manifest(path.read_bytes())
