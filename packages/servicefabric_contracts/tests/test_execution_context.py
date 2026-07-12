import unittest
from servicefabric_contracts.execution_context import ParentExecutionContext
class ExecutionContextTests(unittest.TestCase):
    def test_depth_is_bounded(self): self.assertEqual(ParentExecutionContext(root_correlation_id="corr-1", depth=0).depth, 0)
