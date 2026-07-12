"""Deterministic effect verification and reconciliation using bounded adapters."""

from __future__ import annotations

import hashlib,json
from dataclasses import dataclass
from datetime import datetime

from servicefabric_contracts import EffectReceipt,EvidenceRecord,ReconciliationRecord
from servicefabric_contracts.durable_operations import ReconciliationRecordSpec
from servicefabric_contracts.effect_receipt import EffectReceiptSpec
from servicefabric_contracts.errors import ToolError
from servicefabric_contracts.metadata import OwnerReference,ResourceMetadata
from servicefabric_contracts.observed_effects import ObservedEffect

def _canonical(v:object)->bytes:return (json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode()
def _digest(v:object)->str:return "sha256:"+hashlib.sha256(_canonical(v)).hexdigest()
def _id(prefix:str,v:object)->str:return prefix+"-"+hashlib.sha256(_canonical(v)).hexdigest()[:24]
def _meta(identifier:str)->ResourceMetadata:return ResourceMetadata(id=identifier,name=identifier.replace("-"," ").title(),description="Deterministic effect verification record.",owner_ref=OwnerReference(kind="service",id="reconciliation-service"))

@dataclass(frozen=True,slots=True)
class FakeEffectObservation:
 outcome:str
 provider_operation_ref:str

class DeterministicEffectAdapter:
 def __init__(self,outcomes:dict[str,str]):self._outcomes=dict(outcomes)
 def verify(self,provider_operation_ref:str)->FakeEffectObservation:
  return FakeEffectObservation(self._outcomes.get(provider_operation_ref,"verification_unavailable"),provider_operation_ref)

@dataclass(frozen=True,slots=True)
class ReconciliationResult:
 record:ReconciliationRecord
 evidence:EvidenceRecord
 observed_effect:ObservedEffect|None
 receipt:EffectReceipt|None

class ReconciliationService:
 def __init__(self,adapter:DeterministicEffectAdapter):self._adapter=adapter
 def reconcile(self,*,operation_ref:str,attempt_ref:str,invocation_id:str,tool_id:str,revision_ref:str,declared_effect_ref:str,provider_operation_ref:str,idempotency_digest:str,now:datetime)->ReconciliationResult:
  observation=self._adapter.verify(provider_operation_ref);outcome=observation.outcome
  if outcome not in {"known_committed","known_absent","unknown","verification_unavailable"}:raise ValueError("adapter returned unsupported reconciliation outcome")
  evidence_id=_id("evidence",{"provider":provider_operation_ref,"outcome":outcome})
  evidence=EvidenceRecord(evidence_id=evidence_id,evidence_type="provider_response",source_ref="deterministic-effect-adapter",locator="provider-operation:"+provider_operation_ref,content_digest=_digest({"provider":provider_operation_ref,"outcome":outcome}),collected_at=now,trust_classification="platform",claims=("effect-"+outcome.replace("_","-"),),summary="Bounded deterministic provider verification result.")
  observed=None;receipt=None;error=None;method=None
  if outcome=="known_committed":
   method="fake-provider-query";observed=ObservedEffect(effect_id=_id("effect",provider_operation_ref),declared_effect_ref=declared_effect_ref,effect_type="task-create",target_ref="fixture-task",provider_operation_ref=provider_operation_ref,state="verified",observed_at=now,reversibility="reversible")
  elif outcome=="known_absent":method="fake-provider-query"
  elif outcome=="verification_unavailable":error=ToolError(code="SF-EFFECT-VERIFICATION_UNAVAILABLE",category="effect",message="Effect verification is temporarily unavailable.",retryable=True,retry_classification="dependency_recovery",dependency_ref="deterministic-effect-adapter")
  if outcome in {"known_committed","known_absent"}:
   receipt_id=_id("receipt",{"operation":operation_ref,"provider":provider_operation_ref,"outcome":outcome})
   receipt=EffectReceipt(apiVersion="servicefabric.ai/v1alpha1",kind="EffectReceipt",metadata=_meta(receipt_id),spec=EffectReceiptSpec(receipt_id=receipt_id,invocation_id=invocation_id,tool_id=tool_id,revision_ref=revision_ref,declared_effect_ref=declared_effect_ref,observed_effects=(observed,) if observed else (),verification_status="reconciled",verification_method=method,verified_no_op=outcome=="known_absent",idempotency_digest=idempotency_digest,issued_at=now,evidence_refs=(evidence_id,)))
  reconciliation_id=_id("reconciliation",{"operation":operation_ref,"attempt":attempt_ref,"provider":provider_operation_ref,"outcome":outcome})
  record=ReconciliationRecord(apiVersion="servicefabric.ai/v1alpha1",kind="ReconciliationRecord",metadata=_meta(reconciliation_id),spec=ReconciliationRecordSpec(reconciliation_id=reconciliation_id,operation_ref=operation_ref,attempt_ref=attempt_ref,declared_effect_ref=declared_effect_ref,observed_effect=observed,provider_operation_ref=provider_operation_ref,idempotency_digest=idempotency_digest,outcome=outcome,verification_method=method,verified_at=now,effect_receipt_ref=receipt.spec.receipt_id if receipt else None,evidence_refs=(evidence_id,),error=error,safe_reason={"known_committed":"Provider confirmed the effect was committed.","known_absent":"Provider confirmed no effect occurred.","unknown":"The effect outcome remains unknown.","verification_unavailable":"Effect verification is unavailable."}[outcome]))
  return ReconciliationResult(record,evidence,observed,receipt)
