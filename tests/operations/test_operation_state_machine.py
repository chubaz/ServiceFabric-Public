import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from servicefabric_contracts import OperationEvent, ServiceFabricOperation
from servicefabric_contracts.errors import ToolError
from servicefabric_operations import DurableOperationStore, IllegalTransitionError, LEGAL_TRANSITIONS, OperationStateMachine

NOW=datetime(2030,1,1,12,0,tzinfo=timezone.utc); D1="sha256:"+"1"*64
META={"id":"operation-1","name":"Fixture operation","description":"State fixture.","owner_ref":{"kind":"service","id":"operation-controller"}}
STATES=set(LEGAL_TRANSITIONS)
def operation(): return ServiceFabricOperation.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ServiceFabricOperation","metadata":META,"spec":{"operation_id":"operation-1","request_ref":"request-1","invocation_ref":"invocation-1","tool_id":"project.create_task","revision_ref":"1.0.0","state":"accepted","created_at":NOW,"updated_at":NOW,"cancellation":{"cancellable":True,"cancellation_state":"not_requested"}}})
def event(): return OperationEvent.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"OperationEvent","metadata":{**META,"id":"event-1"},"spec":{"event_id":"event-1","operation_ref":"operation-1","sequence":1,"operation_version":1,"event_type":"accepted","recorded_at":NOW,"event_digest":D1}})
def machine(root): store=DurableOperationStore(Path(root)); store.publish(operation(),event()); return OperationStateMachine(store),store

class OperationStateMachineTests(unittest.TestCase):
    def test_transition_matrix_is_explicit_for_every_state_pair(self):
        for source in STATES:
            for target in STATES:
                self.assertEqual(OperationStateMachine.is_legal(source,target),target in LEGAL_TRANSITIONS[source])
        for terminal in {"succeeded","partially_succeeded","failed","cancelled","timed_out"}: self.assertFalse(LEGAL_TRANSITIONS[terminal])

    def test_allowed_queue_and_running_transitions_append_history(self):
        with tempfile.TemporaryDirectory() as root:
            controller,store=machine(root)
            controller.transition("operation-1","queued",expected_version=1,now=NOW+timedelta(seconds=1),actor_ref="controller",reason_code="policy-allowed",safe_reason="Queued.")
            value=controller.transition("operation-1","running",expected_version=2,now=NOW+timedelta(seconds=2),actor_ref="controller",reason_code="attempt-started",safe_reason="Running.",attempt_ref="attempt-1")
            self.assertEqual(value.spec.state,"running"); self.assertEqual(len(store.events("operation-1")),3); store.replay("operation-1")

    def test_required_approval_cannot_be_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            controller,_=machine(root); controller.transition("operation-1","waiting_for_approval",expected_version=1,now=NOW+timedelta(seconds=1),actor_ref="controller",reason_code="approval-required",safe_reason="Waiting.")
            with self.assertRaises(IllegalTransitionError): controller.transition("operation-1","queued",expected_version=2,now=NOW+timedelta(seconds=2),actor_ref="controller",reason_code="approved",safe_reason="Queued.")
            controller.transition("operation-1","queued",expected_version=2,now=NOW+timedelta(seconds=2),actor_ref="controller",reason_code="approved",safe_reason="Queued.",approval_binding_ref="approval-binding-1")

    def test_illegal_skip_and_stale_version_preserve_history(self):
        with tempfile.TemporaryDirectory() as root:
            controller,store=machine(root)
            with self.assertRaises(IllegalTransitionError): controller.transition("operation-1","succeeded",expected_version=1,now=NOW,actor_ref="controller",reason_code="done",safe_reason="Done.",result_ref="result-1")
            with self.assertRaises(IllegalTransitionError): controller.transition("operation-1","queued",expected_version=2,now=NOW,actor_ref="controller",reason_code="queue",safe_reason="Queued.")
            self.assertEqual(len(store.events("operation-1")),1)

    def test_terminal_result_and_error_invariants(self):
        with tempfile.TemporaryDirectory() as root:
            controller,_=machine(root); controller.transition("operation-1","queued",expected_version=1,now=NOW+timedelta(seconds=1),actor_ref="controller",reason_code="queue",safe_reason="Queued."); controller.transition("operation-1","running",expected_version=2,now=NOW+timedelta(seconds=2),actor_ref="controller",reason_code="run",safe_reason="Running.",attempt_ref="attempt-1")
            with self.assertRaises(IllegalTransitionError): controller.transition("operation-1","failed",expected_version=3,now=NOW+timedelta(seconds=3),actor_ref="controller",reason_code="failed",safe_reason="Failed.",attempt_ref="attempt-1")
            error=ToolError(code="SF-EXEC-FAILED",category="execution",message="Execution failed.")
            failed=controller.transition("operation-1","failed",expected_version=3,now=NOW+timedelta(seconds=3),actor_ref="controller",reason_code="failed",safe_reason="Failed.",attempt_ref="attempt-1",error=error)
            self.assertIsNotNone(failed.spec.completed_at)
            with self.assertRaises(IllegalTransitionError): controller.transition("operation-1","queued",expected_version=4,now=NOW+timedelta(seconds=4),actor_ref="controller",reason_code="retry",safe_reason="Retry.")

    def test_recovery_requires_reconciliation_for_uncertain_effects(self):
        self.assertEqual(OperationStateMachine.recovery_decision(operation().model_copy(update={"spec":operation().spec.model_copy(update={"state":"running"})}),effects_known_absent=False,retry_eligible=True),"reconcile")

if __name__=="__main__": unittest.main()
