import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from servicefabric_contracts.effect_receipt import EffectReceiptSpec
class ReceiptTests(unittest.TestCase):
    def test_verified_requires_method_and_effect(self):
        base=dict(receipt_id="r-1", invocation_id="i-1", tool_id="project.create_task", revision_ref="1.0.0", declared_effect_ref="task-create", issued_at=datetime.now(timezone.utc))
        with self.assertRaises(ValidationError): EffectReceiptSpec(**base, verification_status="verified")
