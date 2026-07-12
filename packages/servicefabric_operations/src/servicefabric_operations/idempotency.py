"""Atomic local idempotency reservation with exact intent binding."""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from servicefabric_contracts import IdempotencyRecord
from servicefabric_contracts.durable_operations import IdempotencyRecordSpec
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata

from .store import CorruptOperationError, OperationStoreError, _envelope, canonical_json


class IdempotencyConflictError(RuntimeError): pass


def idempotency_digest(raw_key: str, *, scope: str, trusted_adapter: bool) -> str:
    if not trusted_adapter: raise IdempotencyConflictError("trusted adapter must digest idempotency keys")
    if not raw_key or len(raw_key)>256: raise IdempotencyConflictError("idempotency key length is invalid")
    value=f"servicefabric-idempotency-v1\0{scope}\0{raw_key}".encode()
    return "sha256:"+hashlib.sha256(value).hexdigest()


def request_intent_digest(value: object) -> str:
    return "sha256:"+hashlib.sha256(b"servicefabric-intent-v1\0"+canonical_json(value)).hexdigest()


@dataclass(frozen=True,slots=True)
class ReservationResult:
    outcome: str
    record: IdempotencyRecord


class IdempotencyRepository:
    def __init__(self,root:Path): self._root=root.resolve(strict=False); self._root.mkdir(parents=True,exist_ok=True); self._lock=threading.RLock()
    def _path(self,digest:str)->Path:
        if not digest.startswith("sha256:") or len(digest)!=71: raise IdempotencyConflictError("invalid idempotency digest")
        return self._root/(digest[7:]+".json")
    def _read(self,path:Path)->IdempotencyRecord:
        import json
        try:
            env=json.loads(path.read_text()); payload=env["payload"]
            expected="sha256:"+hashlib.sha256(canonical_json(payload)).hexdigest()
            if env["digest"]!=expected: raise CorruptOperationError("idempotency record digest mismatch")
            return IdempotencyRecord.model_validate(payload)
        except CorruptOperationError: raise
        except Exception as exc: raise CorruptOperationError("idempotency record is corrupt") from exc
    def _write(self,path:Path,record:IdempotencyRecord)->None:
        import os,tempfile
        content=_envelope(record.model_dump(mode="json",by_alias=True))
        fd,name=tempfile.mkstemp(prefix=".pending-",dir=self._root)
        try:
            with os.fdopen(fd,"wb") as handle: handle.write(content); handle.flush(); os.fsync(handle.fileno())
            os.replace(name,path)
        finally:
            Path(name).unlink(missing_ok=True)
    def reserve(self,*,key_digest:str,intent_digest:str,scope:str,caller_ref:str,namespace_ref:str|None,request_ref:str,operation_ref:str,now:datetime,expires_at:datetime)->ReservationResult:
        path=self._path(key_digest)
        with self._lock:
            if path.exists():
                record=self._read(path)
                if record.spec.intent_digest!=intent_digest: raise IdempotencyConflictError("idempotency key was already used for different intent")
                outcome="duplicate_completed" if record.spec.state=="completed" else "duplicate_in_progress"
                return ReservationResult(outcome,record)
            identifier="idempotency-"+key_digest[7:31]
            record=IdempotencyRecord(apiVersion="servicefabric.ai/v1alpha1",kind="IdempotencyRecord",metadata=ResourceMetadata(id=identifier,name="Idempotency reservation",description="Opaque exact-intent deduplication record.",owner_ref=OwnerReference(kind="service",id="idempotency-service")),spec=IdempotencyRecordSpec(record_id=identifier,key_digest=key_digest,intent_digest=intent_digest,scope=scope,caller_ref=caller_ref,namespace_ref=namespace_ref,request_ref=request_ref,operation_ref=operation_ref,state="in_progress",created_at=now,expires_at=expires_at))
            self._write(path,record); return ReservationResult("reserved",record)
    def complete(self,key_digest:str,*,intent_digest:str,result_ref:str)->IdempotencyRecord:
        path=self._path(key_digest)
        with self._lock:
            record=self._read(path)
            if record.spec.intent_digest!=intent_digest: raise IdempotencyConflictError("idempotency intent conflict")
            updated=record.model_copy(update={"spec":record.spec.model_copy(update={"state":"completed","completed_result_ref":result_ref})})
            updated=IdempotencyRecord.model_validate(updated.model_dump(mode="python",by_alias=True)); self._write(path,updated); return updated
    def expire(self,key_digest:str,*,now:datetime,effect_uncertain:bool=False)->None:
        path=self._path(key_digest)
        with self._lock:
            record=self._read(path)
            if effect_uncertain or now<record.spec.expires_at: raise OperationStoreError("idempotency record is still retained")
            path.unlink()
