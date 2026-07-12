#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.agent.common import milestone,run,canonical
def verify(mid,phase):
 checks=[]; ok=True
 for item in milestone(mid)["verification"][phase]:
  if item.get("planned"): checks.append({"name":item["name"],"status":"planned"});continue
  result=run(item["command"]); passed=result.returncode==0; ok=ok and (passed or not item["required"])
  checks.append({"name":item["name"],"status":"passed" if passed else "failed","returncode":result.returncode,"output":(result.stdout+result.stderr)[-2000:]})
 return {"milestone":mid,"phase":phase,"ok":ok,"checks":checks}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--milestone",required=True);p.add_argument("--phase",choices=["readiness","completion"],default="completion");p.add_argument("--format",choices=["text","json"],default="text");p.add_argument("--output");a=p.parse_args();r=verify(a.milestone,a.phase)
 if a.output: Path(a.output).write_text(canonical(r),encoding="utf-8")
 print(json.dumps(r,sort_keys=True) if a.format=="json" else f"Verification {a.milestone}/{a.phase}: {'passed' if r['ok'] else 'failed'}")
 raise SystemExit(0 if r["ok"] else 1)
