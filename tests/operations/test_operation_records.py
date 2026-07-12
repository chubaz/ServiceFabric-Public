import json,tempfile,unittest
from pathlib import Path
from servicefabric_contracts import PolicyDecision
from servicefabric_operations import CorruptOperationError,ImmutableRecordRepository,OperationConflictError
FIXTURE=Path(__file__).resolve().parents[2]/"packages/servicefabric_contracts/tests/fixtures/policy_decision_project_task.json"
def policy_payload():return json.loads(FIXTURE.read_text())
class ImmutableRecordTests(unittest.TestCase):
 def test_record_survives_restart_and_is_immutable(self):
  with tempfile.TemporaryDirectory() as root:
   record=PolicyDecision.model_validate(policy_payload());repo=ImmutableRecordRepository(Path(root));repo.put(record,kind="PolicyDecision",identifier=record.spec.decision_id,operation_ref="operation-1");loaded=ImmutableRecordRepository(Path(root)).get(kind="PolicyDecision",identifier=record.spec.decision_id,model=PolicyDecision);self.assertEqual(loaded,record);repo.put(record,kind="PolicyDecision",identifier=record.spec.decision_id,operation_ref="operation-1")
 def test_changed_record_cannot_replace_history(self):
  with tempfile.TemporaryDirectory() as root:
   record=PolicyDecision.model_validate(policy_payload());repo=ImmutableRecordRepository(Path(root));repo.put(record,kind="PolicyDecision",identifier=record.spec.decision_id);changed=record.model_copy(update={"metadata":record.metadata.model_copy(update={"description":"Changed"})})
   with self.assertRaises(OperationConflictError):repo.put(changed,kind="PolicyDecision",identifier=record.spec.decision_id)
if __name__=="__main__":unittest.main()
