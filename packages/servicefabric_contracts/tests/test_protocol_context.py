import unittest
from pydantic import ValidationError
from servicefabric_contracts.protocol import ProtocolContext
class ProtocolTests(unittest.TestCase):
    def test_authorization_header_is_rejected(self):
        with self.assertRaises(ValidationError): ProtocolContext(protocol="http", adapter_ref="rest", projection_metadata={"authorization":"Bearer x"})
