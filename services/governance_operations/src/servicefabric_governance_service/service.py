"""Internal governance and durable-operation service facade."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from servicefabric_contracts import OperationEvent,PolicyDecision,PolicyEvaluationRequest,ServiceFabricOperation
from servicefabric_governance import ApprovalService,TrustedApprover,TrustedPolicyInput,VersionedPolicyEvaluator
from servicefabric_operations import CancellationController,DurableOperationStore,IdempotencyRepository,OperationStateMachine,ReconciliationService
@dataclass(frozen=True,slots=True)
class SubmissionResult:
 outcome:str
 operation_ref:str
 operation:ServiceFabricOperation
class GovernanceOperationsService:
 def __init__(self,*,evaluator:VersionedPolicyEvaluator,approvals:ApprovalService,operations:DurableOperationStore,idempotency:IdempotencyRepository,reconciliation:ReconciliationService):
  self._evaluator=evaluator;self._approvals=approvals;self._operations=operations;self._idempotency=idempotency;self._state=OperationStateMachine(operations);self._cancellation=CancellationController(operations,self._state);self._reconciliation=reconciliation;self._receipts={}
 def evaluate_policy(self,request:PolicyEvaluationRequest,*,trusted_adapter_ref:str,now:datetime)->PolicyDecision:return self._evaluator.evaluate(TrustedPolicyInput.from_authenticated_adapter(request,adapter_ref=trusted_adapter_ref),now=now)
 def submit_operation(self,operation:ServiceFabricOperation,initial_event:OperationEvent,*,key_digest:str,intent_digest:str,caller_ref:str,namespace_ref:str|None,now:datetime,expires_at:datetime)->SubmissionResult:
  reservation=self._idempotency.reserve(key_digest=key_digest,intent_digest=intent_digest,scope="caller",caller_ref=caller_ref,namespace_ref=namespace_ref,request_ref=operation.spec.request_ref,operation_ref=operation.spec.operation_id,now=now,expires_at=expires_at)
  if reservation.outcome=="reserved":self._operations.publish(operation,initial_event);return SubmissionResult("accepted",operation.spec.operation_id,operation)
  existing,_=self._operations.get(reservation.record.spec.operation_ref);return SubmissionResult(reservation.outcome,existing.spec.operation_id,existing)
 def get_operation(self,operation_ref:str):return self._operations.get(operation_ref)
 def list_operation_events(self,operation_ref:str):return self._operations.events(operation_ref)
 def create_approval_request(self,*args,**kwargs):return self._approvals.create_request(*args,**kwargs)
 def record_approval_decision(self,*args,**kwargs):return self._approvals.decide(*args,**kwargs)
 def create_approval_binding(self,*args,**kwargs):return self._approvals.bind(*args,**kwargs)
 def request_cancellation(self,operation_ref:str,**kwargs):return self._cancellation.request(operation_ref,**kwargs)
 def transition(self,operation_ref:str,to_state:str,**kwargs):return self._state.transition(operation_ref,to_state,**kwargs)
 def reconcile(self,**kwargs):
  result=self._reconciliation.reconcile(**kwargs)
  if result.receipt:self._receipts.setdefault(result.record.spec.operation_ref,[]).append(result.receipt)
  return result
 def effect_receipts(self,operation_ref:str):return tuple(self._receipts.get(operation_ref,()))
