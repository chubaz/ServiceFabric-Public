import unittest
from datetime import datetime,timezone
from servicefabric_operations import DeterministicEffectAdapter,ReconciliationService,RetryPlanner
from tests.operations.test_operation_attempts import failed
NOW=datetime(2030,1,1,12,0,tzinfo=timezone.utc);DIGEST="sha256:"+"1"*64
def reconcile(outcome):
 service=ReconciliationService(DeterministicEffectAdapter({"provider-op-1":outcome}))
 return service.reconcile(operation_ref="operation-1",attempt_ref="attempt-1",invocation_id="invocation-1",tool_id="project.create_task",revision_ref="1.0.0",declared_effect_ref="task-create",provider_operation_ref="provider-op-1",idempotency_digest=DIGEST,now=NOW)
class ReconciliationTests(unittest.TestCase):
 def test_known_committed_produces_observation_receipt_and_evidence(self):
  result=reconcile("known_committed");self.assertEqual(result.observed_effect.state,"verified");self.assertEqual(result.receipt.spec.verification_status,"reconciled");self.assertEqual(result.record.spec.effect_receipt_ref,result.receipt.spec.receipt_id)
 def test_known_absent_produces_verified_noop_and_unlocks_retry(self):
  result=reconcile("known_absent");self.assertTrue(result.receipt.spec.verified_no_op);self.assertIsNone(result.observed_effect)
  self.assertTrue(RetryPlanner(maximum_attempts=3).decide(failed(),now=NOW,deadline=None,cancellation_requested=False).eligible)
 def test_unknown_has_no_receipt_and_remains_blocked(self):
  result=reconcile("unknown");self.assertIsNone(result.receipt);self.assertEqual(result.record.spec.outcome,"unknown");self.assertEqual(RetryPlanner(maximum_attempts=3).decide(failed(uncertainty="possible"),now=NOW,deadline=None,cancellation_requested=False).reason,"reconciliation-required")
 def test_verification_unavailable_fails_closed(self):
  result=reconcile("verification_unavailable");self.assertIsNotNone(result.record.spec.error);self.assertIsNone(result.receipt)
 def test_timeout_before_dispatch_is_known_absent_while_after_dispatch_is_unknown(self):
  before=reconcile("known_absent");after=reconcile("unknown");self.assertTrue(before.receipt.spec.verified_no_op);self.assertIsNone(after.receipt)
 def test_output_is_deterministic(self):self.assertEqual(reconcile("known_committed"),reconcile("known_committed"))
if __name__=="__main__":unittest.main()
