from __future__ import annotations
import hashlib,json,re,subprocess,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SECRET=re.compile(r"password|secret|token|api[_-]?key|authorization|cookie",re.I)
def canonical(value): return json.dumps(value,indent=2,sort_keys=True)+"\n"
def read_json(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))
def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def safe_path(value):
 p=(ROOT/value).resolve()
 if p!=ROOT and ROOT not in p.parents: raise ValueError("path escapes repository")
 return p
def run(command,cwd=ROOT):
 if not isinstance(command,list) or not command or not all(isinstance(x,str) and x for x in command): raise ValueError("command must be a non-empty string array")
 return subprocess.run(command,cwd=cwd,text=True,capture_output=True,check=False)
def git(*args): return run(["git",*args])
def redact(value): return "[REDACTED]" if SECRET.search(str(value)) else str(value)
def atomic_json(path,value):
 path=safe_path(path); path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=path.parent,prefix=".agent-")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as handle: handle.write(canonical(value))
  os.replace(name,path)
 finally:
  if os.path.exists(name): os.unlink(name)
def milestones(): return read_json("config/agent/milestones.json")["milestones"]
def milestone(mid):
 for item in milestones():
  if item["id"]==mid:return item
 raise KeyError(mid)
def current_id(): return read_json("docs/workplans/status.json")["current_milestone"]
