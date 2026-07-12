import tempfile,threading,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from servicefabric_operations import IdempotencyConflictError,IdempotencyRepository,idempotency_digest,request_intent_digest
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def reserve(repo,key,intent,operation="operation-1"): return repo.reserve(key_digest=key,intent_digest=intent,scope="caller",caller_ref="user-alice",namespace_ref="tenant-demo",request_ref="request-1",operation_ref=operation,now=NOW,expires_at=NOW+timedelta(days=1))
class IdempotencyTests(unittest.TestCase):
 def test_digest_requires_trusted_boundary_and_is_deterministic(self):
  with self.assertRaises(IdempotencyConflictError): idempotency_digest("key",scope="caller",trusted_adapter=False)
  self.assertEqual(idempotency_digest("key",scope="caller",trusted_adapter=True),idempotency_digest("key",scope="caller",trusted_adapter=True))
 def test_duplicate_in_progress_and_completed_return_original(self):
  with tempfile.TemporaryDirectory() as root:
   repo=IdempotencyRepository(Path(root)); key=idempotency_digest("key",scope="caller",trusted_adapter=True); intent=request_intent_digest({"tool":"project.create_task","arguments":{"title":"review"}})
   first=reserve(repo,key,intent); duplicate=reserve(repo,key,intent,"operation-2"); self.assertEqual((first.outcome,duplicate.outcome),("reserved","duplicate_in_progress")); self.assertEqual(duplicate.record.spec.operation_ref,"operation-1")
   repo.complete(key,intent_digest=intent,result_ref="result-1"); self.assertEqual(reserve(repo,key,intent).outcome,"duplicate_completed")
 def test_conflicting_reuse_creates_nothing_new(self):
  with tempfile.TemporaryDirectory() as root:
   repo=IdempotencyRepository(Path(root)); key=idempotency_digest("key",scope="caller",trusted_adapter=True); reserve(repo,key,request_intent_digest({"a":1}))
   with self.assertRaises(IdempotencyConflictError): reserve(repo,key,request_intent_digest({"a":2}))
   self.assertEqual(len(list(Path(root).glob("*.json"))),1)
 def test_concurrent_identical_reservations_share_one_operation(self):
  with tempfile.TemporaryDirectory() as root:
   repo=IdempotencyRepository(Path(root)); key=idempotency_digest("race",scope="caller",trusted_adapter=True); intent=request_intent_digest({"a":1}); results=[]
   threads=[threading.Thread(target=lambda i=i:results.append(reserve(repo,key,intent,f"operation-{i}"))) for i in range(8)]
   [t.start() for t in threads]; [t.join() for t in threads]
   self.assertEqual(sum(r.outcome=="reserved" for r in results),1); self.assertEqual(len({r.record.spec.operation_ref for r in results}),1)
 def test_raw_key_is_not_persisted_and_uncertain_record_cannot_expire(self):
  with tempfile.TemporaryDirectory() as root:
   repo=IdempotencyRepository(Path(root)); raw="private-raw-key"; key=idempotency_digest(raw,scope="caller",trusted_adapter=True); intent=request_intent_digest({"a":1}); reserve(repo,key,intent)
   self.assertNotIn(raw,next(Path(root).glob("*.json")).read_text())
   with self.assertRaises(Exception): repo.expire(key,now=NOW+timedelta(days=2),effect_uncertain=True)
if __name__=="__main__":unittest.main()
