import json,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from servicefabric_client.governance import GovernanceClient
from servicefabric_contracts import OperationEvent,PolicyEvaluationRequest,ServiceFabricOperation
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_governance import ApprovalService,PolicyBundle,TrustedApprover,VersionedPolicyEvaluator
from servicefabric_governance_service import GovernanceOperationsService
from servicefabric_operations import DeterministicEffectAdapter,DurableOperationStore,IdempotencyRepository,ReconciliationService,idempotency_digest,request_intent_digest
NOW=datetime(2030,1,1,12,0,tzinfo=timezone.utc);D1="sha256:"+"1"*64;D2="sha256:"+"2"*64
ROOT=Path(__file__).resolve().parents[2];EVAL=ROOT/"packages/servicefabric_contracts/tests/fixtures/policy_evaluation_request_project_task.json"
def operation(identifier):
 meta={"id":identifier,"name":"Review task operation","description":"Safe deterministic operation.","owner_ref":{"kind":"service","id":"operation-controller"}}
 op=ServiceFabricOperation.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ServiceFabricOperation","metadata":meta,"spec":{"operation_id":identifier,"request_ref":"request-1","invocation_ref":"invocation-1","tool_id":"project.create_task","revision_ref":"1.0.0","state":"accepted","created_at":NOW,"updated_at":NOW,"cancellation":{"cancellable":True,"cancellation_state":"not_requested"}}})
 event=OperationEvent.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"OperationEvent","metadata":{**meta,"id":"event-1"},"spec":{"event_id":"event-1","operation_ref":identifier,"sequence":1,"operation_version":1,"event_type":"accepted","recorded_at":NOW,"event_digest":D1}});return op,event
def build(root,outcome="known_committed"):
 bundle=PolicyBundle(bundle_id="policy-default",version="1.0.0",digest=D1,allowed_scopes=("project-task-create",),approval_effects=("task_create",))
 service=GovernanceOperationsService(evaluator=VersionedPolicyEvaluator((bundle,)),approvals=ApprovalService(),operations=DurableOperationStore(Path(root)/"operations"),idempotency=IdempotencyRepository(Path(root)/"idempotency"),reconciliation=ReconciliationService(DeterministicEffectAdapter({"provider-op-1":outcome})))
 return GovernanceClient(service)
class V3VerticalSliceTests(unittest.TestCase):
 def test_approval_durable_restart_duplicate_success_and_effect_receipt(self):
  with tempfile.TemporaryDirectory() as root:
   client=build(root);evaluation=PolicyEvaluationRequest.model_validate(json.loads(EVAL.read_text()));decision=client.evaluate_policy(evaluation,trusted_adapter_ref="trusted-test",now=NOW);self.assertEqual(decision.spec.outcome,"require_approval")
   op,initial=operation("operation-1");key=idempotency_digest("vertical-key",scope="caller",trusted_adapter=True);intent=request_intent_digest({"tool":"project.create_task","arguments":{"title":"review"}});args=dict(key_digest=key,intent_digest=intent,caller_ref="user-alice",namespace_ref="tenant-demo",now=NOW,expires_at=NOW+timedelta(days=1));self.assertEqual(client.submit_operation(op,initial,**args).outcome,"accepted");self.assertEqual(client.submit_operation(op,initial,**args).outcome,"duplicate_in_progress")
   authority=AuthorityGrant(scopes=("project-task-create",),tenant_ref="tenant-demo",resource_refs=("project-demo",));request=client.create_approval_request(decision,request_ref="request-1",operation_ref="operation-1",caller_ref="user-alice",tenant_ref="tenant-demo",argument_digest=D2,effect_class="task-create",requested_authority=authority,now=NOW,expires_at=NOW+timedelta(minutes=10));approver=TrustedApprover.from_authenticated_adapter(subject_ref="approver-bob",authority_ref="approver-authority-1",authentication_strength="multi_factor",adapter_ref="trusted-test");approved=client.record_approval_decision(request,approver,outcome="approved",now=NOW+timedelta(seconds=1),reason_code="approved-reviewed",safe_reason="Approved.");binding=client.create_approval_binding(request,approved,policy_version="1.0.0")
   client.transition("operation-1","waiting_for_approval",expected_version=1,now=NOW+timedelta(seconds=2),actor_ref="controller",reason_code="approval-required",safe_reason="Waiting.");client.transition("operation-1","queued",expected_version=2,now=NOW+timedelta(seconds=3),actor_ref="controller",reason_code="approved",safe_reason="Queued.",approval_binding_ref=binding.spec.binding_id);client.transition("operation-1","running",expected_version=3,now=NOW+timedelta(seconds=4),actor_ref="controller",reason_code="attempt-started",safe_reason="Running.",attempt_ref="attempt-1")
   reconciled=client.reconcile(operation_ref="operation-1",attempt_ref="attempt-1",invocation_id="invocation-1",tool_id="project.create_task",revision_ref="1.0.0",declared_effect_ref="task-create",provider_operation_ref="provider-op-1",idempotency_digest=key,now=NOW+timedelta(seconds=5));self.assertEqual(reconciled.record.spec.outcome,"known_committed")
   client.transition("operation-1","succeeded",expected_version=4,now=NOW+timedelta(seconds=6),actor_ref="controller",reason_code="completed",safe_reason="Completed.",attempt_ref="attempt-1",result_ref="result-1")
   restarted=build(root);recovered,version=restarted.get_operation("operation-1");self.assertEqual((recovered.spec.state,version),("succeeded",5));self.assertEqual(len(restarted.list_operation_events("operation-1")),5)
 def test_policy_denial_cancellation_timeout_and_uncertain_reconciliation(self):
  with tempfile.TemporaryDirectory() as root:
   client=build(root,"unknown");payload=json.loads(EVAL.read_text());payload["spec"]["required_permissions"][0]["permission_id"]="admin-only";decision=client.evaluate_policy(PolicyEvaluationRequest.model_validate(payload),trusted_adapter_ref="trusted-test",now=NOW);self.assertEqual(decision.spec.outcome,"deny")
   result=client.reconcile(operation_ref="operation-2",attempt_ref="attempt-1",invocation_id="invocation-2",tool_id="project.create_task",revision_ref="1.0.0",declared_effect_ref="task-create",provider_operation_ref="provider-op-1",idempotency_digest=D1,now=NOW);self.assertEqual(result.record.spec.outcome,"unknown");self.assertIsNone(result.receipt)
if __name__=="__main__":unittest.main()
