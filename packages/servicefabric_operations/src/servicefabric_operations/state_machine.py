"""Validated local operation transitions over immutable event history."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from servicefabric_contracts import OperationEvent, OperationTransition, ServiceFabricOperation
from servicefabric_contracts.durable_operations import OperationEventSpec, OperationTransitionSpec
from servicefabric_contracts.errors import ToolError
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata
from servicefabric_contracts.operations import CancellationState

from .store import DurableOperationStore


class IllegalTransitionError(RuntimeError):
    pass


LEGAL_TRANSITIONS = {
    "accepted": {"queued", "waiting_for_approval", "failed", "cancelled", "timed_out"},
    "waiting_for_approval": {"queued", "failed", "cancelled", "timed_out"},
    "queued": {"running", "waiting_for_dependency", "cancelled", "timed_out", "failed"},
    "waiting_for_dependency": {"queued", "running", "cancelled", "timed_out", "failed"},
    "waiting_for_human": {"queued", "cancelled", "timed_out", "failed"},
    "running": {"succeeded", "partially_succeeded", "failed", "cancelled", "timed_out", "waiting_for_dependency", "waiting_for_human"},
    "succeeded": set(), "partially_succeeded": set(), "failed": set(), "cancelled": set(), "timed_out": set(),
}


def _digest(value: object) -> str:
    encoded=(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode()
    return "sha256:"+hashlib.sha256(encoded).hexdigest()


def _metadata(identifier: str) -> ResourceMetadata:
    return ResourceMetadata(id=identifier,name=identifier.replace("-"," ").title(),description="Immutable operation history record.",owner_ref=OwnerReference(kind="service",id="operation-controller"))


class OperationStateMachine:
    def __init__(self, store: DurableOperationStore): self._store=store

    @staticmethod
    def is_legal(from_state: str, to_state: str) -> bool:
        return to_state in LEGAL_TRANSITIONS.get(from_state,set())

    def transition(self, operation_id: str, to_state: str, *, expected_version: int, now: datetime, actor_ref: str, reason_code: str, safe_reason: str, approval_binding_ref: str|None=None, attempt_ref: str|None=None, result_ref: str|None=None, error: ToolError|None=None, cancellation_reason: str|None=None) -> ServiceFabricOperation:
        operation,version=self._store.get(operation_id)
        if version != expected_version: raise IllegalTransitionError("operation version changed")
        source=operation.spec.state
        if not self.is_legal(source,to_state): raise IllegalTransitionError("illegal operation transition")
        if source=="waiting_for_approval" and to_state=="queued" and not approval_binding_ref: raise IllegalTransitionError("approval binding is required")
        if to_state=="running" and not attempt_ref: raise IllegalTransitionError("running transition requires an execution attempt")
        if source=="running" and to_state in {"succeeded","partially_succeeded","failed","cancelled","timed_out"} and not attempt_ref: raise IllegalTransitionError("attempt reference is required")
        if to_state in {"succeeded","partially_succeeded"} and not result_ref: raise IllegalTransitionError("successful terminal state requires a result")
        if to_state=="failed" and error is None: raise IllegalTransitionError("failed state requires an error")
        if to_state in {"cancelled","timed_out"} and not cancellation_reason: raise IllegalTransitionError("cancellation or timeout requires a reason")
        if now.tzinfo is None or now.utcoffset() is None or now < operation.spec.updated_at: raise IllegalTransitionError("transition time is invalid")
        next_version=version+1; transition_id=f"transition-{next_version}"
        transition=OperationTransition(apiVersion="servicefabric.ai/v1alpha1",kind="OperationTransition",metadata=_metadata(transition_id),spec=OperationTransitionSpec(transition_id=transition_id,operation_ref=operation_id,from_state=source,to_state=to_state,expected_version=version,resulting_version=next_version,reason_code=reason_code,safe_reason=safe_reason,transitioned_at=now,actor_ref=actor_ref,approval_binding_ref=approval_binding_ref,attempt_ref=attempt_ref,result_ref=result_ref,error=error))
        previous=self._store.events(operation_id)[-1].spec.event_digest
        event_seed={"operation":operation_id,"version":next_version,"transition":transition.model_dump(mode="json",by_alias=True),"previous":previous}
        event_digest=_digest(event_seed); event_id=f"event-{next_version}"
        event=OperationEvent(apiVersion="servicefabric.ai/v1alpha1",kind="OperationEvent",metadata=_metadata(event_id),spec=OperationEventSpec(event_id=event_id,operation_ref=operation_id,sequence=next_version,operation_version=next_version,event_type="transition",recorded_at=now,previous_event_digest=previous,event_digest=event_digest,transition_ref=transition_id,attempt_ref=attempt_ref,approval_ref=approval_binding_ref))
        terminal=to_state in {"succeeded","partially_succeeded","failed","cancelled","timed_out"}
        cancellation=operation.spec.cancellation
        if cancellation_reason:
            cancellation=CancellationState(cancellable=False,cancellation_requested_at=cancellation.cancellation_requested_at,cancellation_reason=cancellation_reason,cancellation_state="completed")
        spec=operation.spec.model_copy(update={"state":to_state,"updated_at":now,"completed_at":now if terminal else None,"result_ref":result_ref,"error":error,"cancellation":cancellation})
        resulting=operation.model_copy(update={"spec":spec})
        resulting=ServiceFabricOperation.model_validate(resulting.model_dump(mode="python",by_alias=True))
        self._store.append(transition,event,resulting,expected_version=version)
        return resulting

    @staticmethod
    def recovery_decision(operation: ServiceFabricOperation, *, effects_known_absent: bool, retry_eligible: bool) -> str:
        if operation.spec.state != "running": return "resume_observation"
        if effects_known_absent and retry_eligible: return "requeue"
        if not effects_known_absent: return "reconcile"
        return "fail"
