"""Internal governance and durable-operation service facade."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from servicefabric_contracts import EffectReceipt,OperationEvent,PolicyDecision,PolicyEvaluationRequest,ServiceFabricOperation
from servicefabric_governance import ApprovalService,TrustedApprover,TrustedPolicyInput,VersionedPolicyEvaluator
from servicefabric_operations import CancellationController,DurableOperationStore,IdempotencyRepository,OperationStateMachine,ReconciliationService
@dataclass(frozen=True,slots=True)
class SubmissionResult:
 outcome:str
 operation_ref:str
 operation:ServiceFabricOperation
class GovernanceOperationsService:
 def __init__(self,*,evaluator:VersionedPolicyEvaluator,approvals:ApprovalService,operations:DurableOperationStore,idempotency:IdempotencyRepository,reconciliation:ReconciliationService,audit_records):
  self._evaluator=evaluator;self._approvals=approvals;self._operations=operations;self._idempotency=idempotency;self._state=OperationStateMachine(operations);self._cancellation=CancellationController(operations,self._state);self._reconciliation=reconciliation;self._audit=audit_records
 def evaluate_policy(self,request:PolicyEvaluationRequest,*,trusted_adapter_ref:str,now:datetime)->PolicyDecision:
  value=self._evaluator.evaluate(TrustedPolicyInput.from_authenticated_adapter(request,adapter_ref=trusted_adapter_ref),now=now);self._audit.put(value,kind="PolicyDecision",identifier=value.spec.decision_id,operation_ref=request.spec.operation_ref);return value
 def submit_operation(self,operation:ServiceFabricOperation,initial_event:OperationEvent,*,key_digest:str,intent_digest:str,caller_ref:str,namespace_ref:str|None,now:datetime,expires_at:datetime)->SubmissionResult:
  reservation=self._idempotency.reserve(key_digest=key_digest,intent_digest=intent_digest,scope="caller",caller_ref=caller_ref,namespace_ref=namespace_ref,request_ref=operation.spec.request_ref,operation_ref=operation.spec.operation_id,now=now,expires_at=expires_at)
  if reservation.outcome=="reserved":self._operations.publish(operation,initial_event);return SubmissionResult("accepted",operation.spec.operation_id,operation)
  existing,_=self._operations.get(reservation.record.spec.operation_ref);return SubmissionResult(reservation.outcome,existing.spec.operation_id,existing)
 def get_operation(self,operation_ref:str):return self._operations.get(operation_ref)
 def list_operation_events(self,operation_ref:str):return self._operations.events(operation_ref)
 def create_approval_request(self,*args,**kwargs):
  value=self._approvals.create_request(*args,**kwargs);self._audit.put(value,kind="ApprovalRequest",identifier=value.spec.approval_request_id,operation_ref=value.spec.operation_ref);return value
 def record_approval_decision(self,*args,**kwargs):
  request=args[0] if args else kwargs.get("request");value=self._approvals.decide(*args,**kwargs);self._audit.put(value,kind="ApprovalDecision",identifier=value.spec.approval_decision_id,operation_ref=request.spec.operation_ref);return value
 def create_approval_binding(self,*args,**kwargs):
  request=args[0] if args else kwargs.get("request");value=self._approvals.bind(*args,**kwargs);self._audit.put(value,kind="ApprovalBinding",identifier=value.spec.binding_id,operation_ref=request.spec.operation_ref);return value
 def request_cancellation(self,operation_ref:str,**kwargs):return self._cancellation.request(operation_ref,**kwargs)
 def transition(self,operation_ref:str,to_state:str,**kwargs):return self._state.transition(operation_ref,to_state,**kwargs)
 def reconcile(self,**kwargs):
  result=self._reconciliation.reconcile(**kwargs)
  operation_ref=result.record.spec.operation_ref;self._audit.put(result.record,kind="ReconciliationRecord",identifier=result.record.spec.reconciliation_id,operation_ref=operation_ref);self._audit.put(result.evidence,kind="EvidenceRecord",identifier=result.evidence.evidence_id,operation_ref=operation_ref)
  if result.receipt:self._audit.put(result.receipt,kind="EffectReceipt",identifier=result.receipt.spec.receipt_id,operation_ref=operation_ref)
  return result
 def effect_receipts(self,operation_ref:str):return self._audit.list_for_operation(kind="EffectReceipt",operation_ref=operation_ref,model=EffectReceipt)
