import unittest
from servicefabric_contracts.schema_export import SCHEMA_RESOURCES
class InvocationInvariantTests(unittest.TestCase):
    def test_all_invocation_resources_are_exported(self):
        self.assertTrue({"tool-result.schema.json","effect-receipt.schema.json","servicefabric-operation.schema.json"} <= set(SCHEMA_RESOURCES))
