import tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from servicefabric_contracts import ExecutionAttempt
from servicefabric_contracts.errors import ToolError
from servicefabric_operations import AttemptRepository,CancellationController,DurableOperationStore,OperationStateMachine,RetryPlanner
from tests.operations.test_operation_state_machine import event,operation
NOW=datetime(2030,1,1,12,0,tzinfo=timezone.utc)
def failed(number=1,uncertainty="none",retryable=True):
 error=ToolError(code="SF-DEPEND-TEMPORARY",category="dependency",message="Temporary failure.",retryable=retryable,retry_classification="transient" if retryable else None)
 return ExecutionAttempt.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ExecutionAttempt","metadata":{"id":f"attempt-{number}","name":"Attempt","description":"Fixture.","owner_ref":{"kind":"service","id":"controller"}},"spec":{"attempt_id":f"attempt-{number}","operation_ref":"operation-1","invocation_ref":"invocation-1","revision_ref":"1.0.0","attempt_number":number,"state":"failed","started_at":NOW,"completed_at":NOW+timedelta(seconds=1),"retry_eligibility":"blocked_pending_reconciliation" if uncertainty=="possible" else "eligible","error":error.model_dump(mode="json"),"effect_uncertainty":uncertainty}})
class AttemptAndCancellationTests(unittest.TestCase):
 def test_attempt_survives_repository_restart(self):
  with tempfile.TemporaryDirectory() as root:
   repo=AttemptRepository(Path(root));repo.put(failed());self.assertEqual(AttemptRepository(Path(root)).get("operation-1",1),failed())
 def test_retry_is_bounded_and_uses_fake_clock_without_sleep(self):
  planner=RetryPlanner(maximum_attempts=3,backoff_seconds=2);decision=planner.decide(failed(),now=NOW,deadline=NOW+timedelta(minutes=1),cancellation_requested=False)
  self.assertTrue(decision.eligible);self.assertEqual(decision.next_eligible_at,NOW+timedelta(seconds=2));self.assertFalse(planner.decide(failed(3),now=NOW,deadline=None,cancellation_requested=False).eligible)
 def test_uncertain_effect_blocks_retry(self):self.assertEqual(RetryPlanner(maximum_attempts=3).decide(failed(uncertainty="possible"),now=NOW,deadline=None,cancellation_requested=False).reason,"reconciliation-required")
 def test_deadline_and_cancellation_block_retry(self):
  planner=RetryPlanner(maximum_attempts=3);self.assertEqual(planner.decide(failed(),now=NOW,deadline=NOW,cancellation_requested=False).reason,"deadline-exceeded");self.assertEqual(planner.decide(failed(),now=NOW,deadline=None,cancellation_requested=True).reason,"cancelled")
 def test_cancellation_request_and_acknowledgement_are_persistent(self):
  with tempfile.TemporaryDirectory() as root:
   store=DurableOperationStore(Path(root));store.publish(operation(),event());controller=CancellationController(store,OperationStateMachine(store));controller.request("operation-1",expected_version=1,now=NOW+timedelta(seconds=1),reason="Operator requested cancellation.");controller.acknowledge("operation-1",expected_version=2,now=NOW+timedelta(seconds=2));replayed,version=DurableOperationStore(Path(root)).replay("operation-1");self.assertEqual((replayed.spec.cancellation.cancellation_state,version),("acknowledged",3))
if __name__=="__main__":unittest.main()
