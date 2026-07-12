#!/usr/bin/env python3
import argparse,json,re,sys,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.agent.common import ROOT,git,milestone,safe_path,sha256
from scripts.agent.validate_workplans import validate
def inspect(mid,mode="local"):
 m=milestone(mid); diagnostics=[]; start=time.monotonic()
 head=git("rev-parse","HEAD").stdout.strip(); branch=git("branch","--show-current").stdout.strip() or "detached"
 dirty=bool(git("status","--porcelain").stdout.strip())
 if dirty and mode!="ci": diagnostics.append({"severity":"warning","code":"dirty_tree"})
 if git("rev-parse","--verify","origin/main").returncode: diagnostics.append({"severity":"info","code":"base_ref_unavailable"})
 for name in m["required_files"]:
  if not safe_path(name).exists(): diagnostics.append({"severity":"error","code":"missing_file","path":name})
 validate()
 version=(ROOT/"packages/servicefabric_contracts/pyproject.toml").read_text(); expected="0.4.0a1"
 if expected not in version: diagnostics.append({"severity":"error","code":"contract_version"})
 mapping=(ROOT/"docs/architecture/specification-map.md").read_text(encoding="utf-8")
 for relative,digest in re.findall(r"`(\.\./canonical/[^`]+)` \| `([a-f0-9]{64})`",mapping):
  source=(ROOT/"docs/architecture"/relative).resolve()
  if not source.is_file() and relative.endswith("servicefabric-stage11/README.md"):
   source=(ROOT.parent/"servicefabric-stage11/README.md").resolve()
  actual=hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
  if actual!=digest: diagnostics.append({"severity":"error","code":"canonical_hash_mismatch","path":source.relative_to(ROOT).as_posix() if source.exists() else relative})
 return {"branch":branch,"commit":head,"dirty":dirty,"milestone":mid,"mode":mode,"schema_index_sha256":sha256(ROOT/"schemas/servicefabric/v1alpha1/schema-index.json"),"diagnostics":diagnostics,"ok":not any(x["severity"]=="error" for x in diagnostics),"runtime_ms":round((time.monotonic()-start)*1000)}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--milestone",required=True);p.add_argument("--mode",choices=["local","ci"],default="local");p.add_argument("--format",choices=["text","json"],default="text");a=p.parse_args()
 try:r=inspect(a.milestone,a.mode)
 except Exception as exc: print(f"Preflight failed: {exc}",file=sys.stderr);raise SystemExit(1)
 print(json.dumps(r,sort_keys=True) if a.format=="json" else f"Preflight {a.milestone}: {'passed' if r['ok'] else 'blocked'} ({len(r['diagnostics'])} diagnostics)")
 raise SystemExit(0 if r["ok"] else 1)
