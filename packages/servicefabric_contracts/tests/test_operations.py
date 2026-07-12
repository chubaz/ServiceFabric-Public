import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from servicefabric_contracts.operations import CancellationState, ServiceFabricOperationSpec
class OperationTests(unittest.TestCase):
    def test_terminal_state_requires_completion(self):
        now=datetime.now(timezone.utc); base=dict(operation_id="op-1", request_ref="req-1", invocation_ref="inv-1", tool_id="math.calculate", revision_ref="1.0.0", created_at=now, updated_at=now, cancellation=CancellationState(cancellable=True))
        with self.assertRaises(ValidationError): ServiceFabricOperationSpec(**base, state="succeeded")
        self.assertEqual(ServiceFabricOperationSpec(**base, state="running").state, "running")
