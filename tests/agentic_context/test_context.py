import tempfile
import unittest
from pathlib import Path
from servicefabric_agentic_context import build_context_pack
class ContextTests(unittest.TestCase):
 def test_context_is_bounded_and_sorted(self):
  with tempfile.TemporaryDirectory() as root:
   Path(root, "AGENTS.md").write_text("x")
   pack=build_context_pack(root, capability_ids=("z", "a", "a"))
   self.assertEqual(pack.files, ("AGENTS.md",)); self.assertEqual(pack.capability_ids, ("a", "z"))
