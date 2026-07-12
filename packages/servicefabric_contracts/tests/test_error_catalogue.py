import unittest
from pydantic import ValidationError
from servicefabric_contracts.errors import ToolError
class ErrorTests(unittest.TestCase):
    def test_namespaces_and_retry_classification(self):
        self.assertEqual(ToolError(code="SF-VALID-INPUT", category="validation", message="Invalid input").retryable, False)
        with self.assertRaises(ValidationError): ToolError(code="BAD", category="runtime", message="bad")
        with self.assertRaises(ValidationError): ToolError(code="SF-DEPEND-DOWN", category="dependency", message="down", retryable=True)
