#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.agent.common import git,milestone,sha256,ROOT
def report(mid,verification=None):
 m=milestone(mid); names=git("diff","--name-only","main...HEAD").stdout.splitlines(); groups={}
 for name in names:groups.setdefault(name.split('/')[0],[]).append(name)
 return {"milestone":mid,"branch":git("branch","--show-current").stdout.strip() or "detached","base":git("merge-base","main","HEAD").stdout.strip(),"head":git("rev-parse","HEAD").stdout.strip(),"changed_files":groups,"diff_stat":git("diff","--stat","main...HEAD").stdout.strip(),"verification":verification,"schema_index_sha256":sha256(ROOT/"schemas/servicefabric/v1alpha1/schema-index.json"),"deviations":[],"limitations":["No runtime implementation is included."],"rollback":"Revert the pull request.","next_milestone":m["handoff_target"]}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--milestone",required=True);p.add_argument("--verification");p.add_argument("--format",choices=["json","markdown"],default="markdown");a=p.parse_args();v=json.loads(Path(a.verification).read_text()) if a.verification else None;r=report(a.milestone,v)
 print(json.dumps(r,indent=2,sort_keys=True) if a.format=="json" else f"# {r['milestone']} completion report\n\nBranch: `{r['branch']}`\n\nValidation: {('passed' if v and v.get('ok') else 'not supplied')}\n\nRollback: {r['rollback']}")
