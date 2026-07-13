import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from servicefabric_contracts import OperationEvent, OperationTransition, ServiceFabricOperation
from servicefabric_operations import CorruptOperationError, DurableOperationStore, OperationConflictError, StoreLimits


NOW=datetime(2030,1,1,12,0,tzinfo=timezone.utc); D1="sha256:"+"1"*64; D2="sha256:"+"2"*64
META={"id":"operation-1","name":"Fixture operation","description":"Durable fixture.","owner_ref":{"kind":"service","id":"operation-controller"}}
def operation(state="accepted",updated=NOW):
    return ServiceFabricOperation.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ServiceFabricOperation","metadata":META,"spec":{"operation_id":"operation-1","request_ref":"request-1","invocation_ref":"invocation-1","tool_id":"project.create_task","revision_ref":"1.0.0","state":state,"created_at":NOW,"updated_at":updated,"cancellation":{"cancellable":True,"cancellation_state":"not_requested"}}})
def event(sequence=1,previous=None,digest=D1,transition_ref=None):
    ident=f"event-{sequence}"
    return OperationEvent.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"OperationEvent","metadata":{**META,"id":ident},"spec":{"event_id":ident,"operation_ref":"operation-1","sequence":sequence,"operation_version":sequence,"event_type":"accepted" if sequence==1 else "transition","recorded_at":NOW,"previous_event_digest":previous,"event_digest":digest,"transition_ref":transition_ref}})
def transition():
    return OperationTransition.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"OperationTransition","metadata":{**META,"id":"transition-2"},"spec":{"transition_id":"transition-2","operation_ref":"operation-1","from_state":"accepted","to_state":"queued","expected_version":1,"resulting_version":2,"reason_code":"policy-allowed","safe_reason":"Queued.","transitioned_at":NOW,"actor_ref":"operation-controller"}})

class OperationStoreTests(unittest.TestCase):
    def test_publish_restart_append_and_replay(self):
        with tempfile.TemporaryDirectory() as root:
            store=DurableOperationStore(Path(root)); store.publish(operation(),event())
            restarted=DurableOperationStore(Path(root)); self.assertEqual(restarted.get("operation-1")[1],1)
            self.assertEqual(restarted.list_operations()[0][0].spec.operation_id,"operation-1")
            queued=operation("queued"); restarted.append(transition(),event(2,D1,D2,"transition-2"),queued,expected_version=1)
            replayed,version=DurableOperationStore(Path(root)).replay("operation-1")
            self.assertEqual((replayed.spec.state,version),("queued",2)); self.assertEqual(len(restarted.events("operation-1")),2)

    def test_stale_version_and_duplicate_publication_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            store=DurableOperationStore(Path(root)); store.publish(operation(),event())
            with self.assertRaises(OperationConflictError): store.publish(operation(),event())
            with self.assertRaises(OperationConflictError): store.append(transition(),event(2,D1,D2,"transition-2"),operation("queued"),expected_version=2)

    def test_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as root:
            store=DurableOperationStore(Path(root)); store.publish(operation(),event())
            snapshot=next(Path(root).glob("*/snapshot.json")); snapshot.write_text("{}")
            with self.assertRaises(CorruptOperationError): store.get("operation-1")

    def test_operation_limit_and_safe_digest_path(self):
        with tempfile.TemporaryDirectory() as root:
            store=DurableOperationStore(Path(root),limits=StoreLimits(maximum_operations=1)); store.publish(operation(),event())
            directories=[p.name for p in Path(root).iterdir()]
            self.assertEqual(directories,[hashlib.sha256(b"operation-1").hexdigest()]); self.assertNotIn("operation-1",directories[0])

    def test_event_chain_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as root:
            store=DurableOperationStore(Path(root)); store.publish(operation(),event()); store.append(transition(),event(2,D1,D2,"transition-2"),operation("queued"),expected_version=1)
            path=sorted(Path(root).glob("*/events/*.json"))[1]; payload=json.loads(path.read_text()); payload["payload"]["event"]["spec"]["previous_event_digest"]=D2; path.write_text(json.dumps(payload))
            with self.assertRaises(CorruptOperationError): store.events("operation-1")

if __name__=="__main__": unittest.main()
