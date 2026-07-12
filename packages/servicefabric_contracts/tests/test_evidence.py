import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from servicefabric_contracts.evidence import EvidenceRecord
class EvidenceTests(unittest.TestCase):
    def test_locator_rejects_credentials(self):
        with self.assertRaises(ValidationError): EvidenceRecord(evidence_id="e-1", evidence_type="web_resource", source_ref="provider", locator="https://user:pass@example.test", collected_at=datetime.now(timezone.utc), trust_classification="external", summary="source")
