import unittest
from pydantic import ValidationError
from servicefabric_contracts.caller import CallerContext
class CallerTests(unittest.TestCase):
    def test_anonymous_cannot_claim_scopes(self):
        with self.assertRaises(ValidationError): CallerContext(subject_ref="anonymous", principal_type="anonymous", issuer="public", scopes=("tool.invoke",), authentication_strength="none")
