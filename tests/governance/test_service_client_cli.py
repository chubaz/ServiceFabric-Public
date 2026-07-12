import json,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from servicefabric_client.governance import GovernanceClient
from servicefabric_client.governance_cli import execute
from servicefabric_contracts import OperationEvent,ServiceFabricOperation
from servicefabric_governance import ApprovalService,PolicyBundle,VersionedPolicyEvaluator
from servicefabric_governance_service import GovernanceOperationsService
from servicefabric_operations import DeterministicEffectAdapter,DurableOperationStore,IdempotencyRepository,ReconciliationService,idempotency_digest,request_intent_digest
from tests.operations.test_operation_state_machine import event,operation
NOW=datetime(2030,1,1,12,0,tzinfo=timezone.utc);D1="sha256:"+"1"*64
def client(root):
 service=GovernanceOperationsService(evaluator=VersionedPolicyEvaluator((PolicyBundle(bundle_id="policy-default",version="1.0.0",digest=D1,allowed_scopes=("project-task-create",)),)),approvals=ApprovalService(),operations=DurableOperationStore(Path(root)/"operations"),idempotency=IdempotencyRepository(Path(root)/"idempotency"),reconciliation=ReconciliationService(DeterministicEffectAdapter({})))
 return GovernanceClient(service)
class ServiceClientCliTests(unittest.TestCase):
 def test_client_delegates_submission_get_and_events(self):
  with tempfile.TemporaryDirectory() as root:
   value=client(root);key=idempotency_digest("key",scope="caller",trusted_adapter=True);intent=request_intent_digest({"operation":"fixture"});submitted=value.submit_operation(operation(),event(),key_digest=key,intent_digest=intent,caller_ref="user-alice",namespace_ref="tenant-demo",now=NOW,expires_at=NOW+timedelta(days=1));self.assertEqual(submitted.outcome,"accepted");self.assertEqual(value.get_operation("operation-1")[1],1);self.assertEqual(len(value.list_operation_events("operation-1")),1)
 def test_duplicate_submission_delegates_to_same_operation(self):
  with tempfile.TemporaryDirectory() as root:
   value=client(root);key=idempotency_digest("key",scope="caller",trusted_adapter=True);intent=request_intent_digest({"operation":"fixture"});args=dict(key_digest=key,intent_digest=intent,caller_ref="user-alice",namespace_ref="tenant-demo",now=NOW,expires_at=NOW+timedelta(days=1));first=value.submit_operation(operation(),event(),**args);second=value.submit_operation(operation(),event(),**args);self.assertEqual((first.operation_ref,second.operation_ref),("operation-1","operation-1"))
 def test_cli_output_is_deterministic_json(self):
  with tempfile.TemporaryDirectory() as root:
   value=client(root);key=idempotency_digest("key",scope="caller",trusted_adapter=True);intent=request_intent_digest({"operation":"fixture"});value.submit_operation(operation(),event(),key_digest=key,intent_digest=intent,caller_ref="user-alice",namespace_ref="tenant-demo",now=NOW,expires_at=NOW+timedelta(days=1));output=execute(value,["get","operation-1"]);self.assertEqual(json.loads(output)["version"],1);self.assertNotIn(str(Path(root)),output)
 def test_client_has_no_storage_attribute(self):
  with tempfile.TemporaryDirectory() as root:self.assertFalse(hasattr(client(root),"store"));self.assertFalse(hasattr(client(root),"_operations"))
if __name__=="__main__":unittest.main()
