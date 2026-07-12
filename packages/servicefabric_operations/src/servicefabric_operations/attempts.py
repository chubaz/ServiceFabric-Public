"""Persistent bounded attempts, cooperative cancellation, and retry decisions."""

from __future__ import annotations

import hashlib,json,os,tempfile,threading
from dataclasses import dataclass
from datetime import datetime,timedelta
from pathlib import Path

from servicefabric_contracts import ExecutionAttempt,OperationEvent,ServiceFabricOperation
from servicefabric_contracts.durable_operations import ExecutionAttemptSpec,OperationEventDetail,OperationEventSpec
from servicefabric_contracts.errors import ToolError
from servicefabric_contracts.metadata import OwnerReference,ResourceMetadata
from servicefabric_contracts.operations import CancellationState

from .state_machine import OperationStateMachine
from .store import DurableOperationStore,OperationConflictError,_envelope,canonical_json

def _digest(value:object)->str:return "sha256:"+hashlib.sha256(canonical_json(value)).hexdigest()
def _meta(identifier:str)->ResourceMetadata:return ResourceMetadata(id=identifier,name=identifier.replace("-"," ").title(),description="Persistent bounded execution record.",owner_ref=OwnerReference(kind="service",id="operation-controller"))

class AttemptRepository:
 def __init__(self,root:Path,max_attempts:int=8):self._root=root.resolve(strict=False);self._root.mkdir(parents=True,exist_ok=True);self._max=max_attempts;self._lock=threading.RLock()
 def _path(self,operation_ref:str,number:int)->Path:return self._root/(hashlib.sha256(operation_ref.encode()).hexdigest()+f"-{number:04d}.json")
 def put(self,attempt:ExecutionAttempt)->None:
  if attempt.spec.attempt_number>self._max:raise ValueError("attempt limit exceeded")
  path=self._path(attempt.spec.operation_ref,attempt.spec.attempt_number);content=_envelope(attempt.model_dump(mode="json",by_alias=True))
  with self._lock:
   if path.exists():
    if path.read_bytes()==content:return
    raise ValueError("immutable attempt record already exists")
   fd,name=tempfile.mkstemp(prefix=".pending-",dir=self._root)
   try:
    with os.fdopen(fd,"wb") as h:h.write(content);h.flush();os.fsync(h.fileno())
    if path.exists():raise ValueError("immutable attempt record already exists")
    os.replace(name,path)
   finally:Path(name).unlink(missing_ok=True)
 def get(self,operation_ref:str,number:int)->ExecutionAttempt:
  env=json.loads(self._path(operation_ref,number).read_text());payload=env["payload"]
  if env["digest"]!=_digest(payload):raise ValueError("attempt record digest mismatch")
  return ExecutionAttempt.model_validate(payload)
 def count(self,operation_ref:str)->int:return len(list(self._root.glob(hashlib.sha256(operation_ref.encode()).hexdigest()+"-*.json")))

@dataclass(frozen=True,slots=True)
class RetryDecision:
 eligible:bool
 reason:str
 next_eligible_at:datetime|None=None

class RetryPlanner:
 def __init__(self,*,maximum_attempts:int,backoff_seconds:int=1):self.maximum_attempts=maximum_attempts;self.backoff_seconds=backoff_seconds
 def decide(self,attempt:ExecutionAttempt,*,now:datetime,deadline:datetime|None,cancellation_requested:bool)->RetryDecision:
  if cancellation_requested:return RetryDecision(False,"cancelled")
  if deadline is not None and now>=deadline:return RetryDecision(False,"deadline-exceeded")
  if attempt.spec.effect_uncertainty=="possible":return RetryDecision(False,"reconciliation-required")
  if attempt.spec.attempt_number>=self.maximum_attempts:return RetryDecision(False,"attempt-budget-exhausted")
  if attempt.spec.error is None or not attempt.spec.error.retryable:return RetryDecision(False,"non-retryable")
  return RetryDecision(True,"retryable",now+timedelta(seconds=self.backoff_seconds*attempt.spec.attempt_number))

class CancellationController:
 def __init__(self,store:DurableOperationStore,state_machine:OperationStateMachine):self._store=store;self._machine=state_machine
 def request(self,operation_id:str,*,expected_version:int,now:datetime,reason:str)->ServiceFabricOperation:
  operation,version=self._store.get(operation_id)
  if version!=expected_version or not operation.spec.cancellation.cancellable:raise OperationConflictError("operation cannot be cancelled")
  cancellation=CancellationState(cancellable=True,cancellation_requested_at=now,cancellation_reason=reason,cancellation_state="requested")
  result=operation.model_copy(update={"spec":operation.spec.model_copy(update={"cancellation":cancellation,"updated_at":now})})
  previous=self._store.events(operation_id)[-1].spec.event_digest;sequence=version+1;event_id=f"event-{sequence}";digest=_digest({"operation":operation_id,"sequence":sequence,"kind":"cancellation","state":"requested","previous":previous})
  event=OperationEvent(apiVersion="servicefabric.ai/v1alpha1",kind="OperationEvent",metadata=_meta(event_id),spec=OperationEventSpec(event_id=event_id,operation_ref=operation_id,sequence=sequence,operation_version=sequence,event_type="cancellation",recorded_at=now,previous_event_digest=previous,event_digest=digest,details=(OperationEventDetail(key="state",value="requested"),OperationEventDetail(key="reason",value=reason))))
  self._store.append_observation(event,resulting=result,expected_version=version);return result
 def acknowledge(self,operation_id:str,*,expected_version:int,now:datetime)->ServiceFabricOperation:
  operation,version=self._store.get(operation_id)
  if version!=expected_version or operation.spec.cancellation.cancellation_state!="requested":raise OperationConflictError("cancellation is not pending")
  cancellation=operation.spec.cancellation.model_copy(update={"cancellation_state":"acknowledged"});result=operation.model_copy(update={"spec":operation.spec.model_copy(update={"cancellation":cancellation,"updated_at":now})})
  previous=self._store.events(operation_id)[-1].spec.event_digest;sequence=version+1;event_id=f"event-{sequence}";digest=_digest({"operation":operation_id,"sequence":sequence,"kind":"cancellation","state":"acknowledged","previous":previous})
  event=OperationEvent(apiVersion="servicefabric.ai/v1alpha1",kind="OperationEvent",metadata=_meta(event_id),spec=OperationEventSpec(event_id=event_id,operation_ref=operation_id,sequence=sequence,operation_version=sequence,event_type="cancellation",recorded_at=now,previous_event_digest=previous,event_digest=digest,details=(OperationEventDetail(key="state",value="acknowledged"),OperationEventDetail(key="reason",value=operation.spec.cancellation.cancellation_reason))))
  self._store.append_observation(event,resulting=result,expected_version=version);return result
