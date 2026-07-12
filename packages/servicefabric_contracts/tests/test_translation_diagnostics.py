import unittest
from servicefabric_contracts.translation_diagnostics import diagnostic
class DiagnosticTests(unittest.TestCase):
 def test_diagnostics_are_structured(self): self.assertEqual(diagnostic("LEGACY_INVALID_JSON","error","Invalid.","","Fix it.").severity,"error")
