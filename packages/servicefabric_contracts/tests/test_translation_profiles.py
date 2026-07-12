import unittest
from servicefabric_contracts.translation_profiles import TEMPLATE_PROFILE
class ProfileTests(unittest.TestCase):
 def test_profiles_are_allowlisted(self): self.assertEqual(TEMPLATE_PROFILE["quant_vite_base"].value,"legacy_composite_ui_python")
