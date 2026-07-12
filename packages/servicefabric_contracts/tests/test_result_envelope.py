import unittest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from servicefabric_contracts.results import ToolResult
class ResultTests(unittest.TestCase):
    def base(self):
        now=datetime.now(timezone.utc); return dict(apiVersion="servicefabric.ai/v1alpha1", kind="ToolResult", invocation_id="inv-1", tool_id="math.calculate", revision_ref="1.0.0", started_at=now, completed_at=now, duration=timedelta(0))
    def test_status_invariants(self):
        self.assertEqual(ToolResult(**self.base(), status="success").status, "success")
        with self.assertRaises(ValidationError): ToolResult(**self.base(), status="error")
        with self.assertRaises(ValidationError): ToolResult(**self.base(), status="partial")
