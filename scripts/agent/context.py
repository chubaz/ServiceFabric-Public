#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import hashlib
from scripts.agent.common import milestone,safe_path,sha256
def describe(path, relative, reason):
 if path.is_file(): return {"path":relative,"size":path.stat().st_size,"sha256":sha256(path),"reason":reason}
 files=sorted(item for item in path.rglob("*") if item.is_file())
 digest=hashlib.sha256();size=0
 for item in files:
  size+=item.stat().st_size;digest.update(item.relative_to(path).as_posix().encode());digest.update(bytes.fromhex(sha256(item)))
 return {"path":relative,"size":size,"sha256":digest.hexdigest(),"reason":reason,"file_count":len(files)}
def context(mid):
 m=milestone(mid); files=[]
 for item in m["context_files"]:
  p=safe_path(item["path"]); files.append(describe(p,item["path"],item["reason"]))
 return {"milestone":mid,"workplan":m["workplan"],"files":files,"allowed_paths":m["allowed_paths"],"forbidden_paths":m["forbidden_paths"]}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--milestone",required=True);p.add_argument("--format",choices=["text","json"],default="text");a=p.parse_args();r=context(a.milestone)
 print(json.dumps(r,sort_keys=True) if a.format=="json" else "\n".join(x["path"] for x in r["files"]))
