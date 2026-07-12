import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class PiBoundaryTests(unittest.TestCase):
 def test_extension_delegates_without_business_logic(self):
  text=(ROOT/"integrations/pi-servicefabric/index.ts").read_text();self.assertIn("invoke(toolId, args)",text);self.assertNotIn("fetch(",text);self.assertNotIn("tools/list",text)
