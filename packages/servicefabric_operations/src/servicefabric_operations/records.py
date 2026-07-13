"""Immutable local repository for governance, evidence, and receipt records."""
from __future__ import annotations
import hashlib,json,os,tempfile,threading
from pathlib import Path
from pydantic import BaseModel
from .store import CorruptOperationError,OperationConflictError,_envelope,canonical_json
class ImmutableRecordRepository:
 def __init__(self,root:Path,max_records:int=10000):self._root=root.resolve(strict=False);self._root.mkdir(parents=True,exist_ok=True);self._max=max_records;self._lock=threading.RLock()
 def _path(self,kind:str,identifier:str)->Path:
  key=hashlib.sha256(f"{kind}\0{identifier}".encode()).hexdigest();return self._root/(key+".json")
 def put(self,record:BaseModel,*,kind:str,identifier:str,operation_ref:str|None=None)->None:
  payload={"kind":kind,"identifier":identifier,"operation_ref":operation_ref,"record":record.model_dump(mode="json",by_alias=True)};path=self._path(kind,identifier);content=_envelope(payload)
  with self._lock:
   if path.exists():
    if path.read_bytes()==content:return
    raise OperationConflictError("immutable audit record already exists with different content")
   if len(list(self._root.glob("*.json")))>=self._max:raise OperationConflictError("audit record retention limit reached")
   fd,name=tempfile.mkstemp(prefix=".pending-",dir=self._root)
   try:
    with os.fdopen(fd,"wb") as h:h.write(content);h.flush();os.fsync(h.fileno())
    if path.exists():raise OperationConflictError("immutable audit record already exists")
    os.replace(name,path)
   finally:Path(name).unlink(missing_ok=True)
 def _payload(self,path:Path)->dict:
  try:
   env=json.loads(path.read_text());payload=env["payload"]
   expected="sha256:"+hashlib.sha256(canonical_json(payload)).hexdigest()
   if env["digest"]!=expected:raise CorruptOperationError("audit record digest mismatch")
   return payload
  except CorruptOperationError:raise
  except Exception as exc:raise CorruptOperationError("audit record is corrupt") from exc
 def get(self,*,kind:str,identifier:str,model:type[BaseModel])->BaseModel:return model.model_validate(self._payload(self._path(kind,identifier))["record"])
 def list_by_kind(self,*,kind:str,model:type[BaseModel])->tuple[BaseModel,...]:
  """Return immutable records of one canonical kind in deterministic order."""
  values=[]
  for path in sorted(self._root.glob("*.json")):
   payload=self._payload(path)
   if payload["kind"]==kind:values.append(model.model_validate(payload["record"]))
  return tuple(sorted(values,key=lambda value:value.metadata.id))
 def list_for_operation(self,*,kind:str,operation_ref:str,model:type[BaseModel])->tuple[BaseModel,...]:
  values=[]
  for path in sorted(self._root.glob("*.json")):
   payload=self._payload(path)
   if payload["kind"]==kind and payload["operation_ref"]==operation_ref:values.append(model.model_validate(payload["record"]))
  return tuple(values)
