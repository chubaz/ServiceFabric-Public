#!/usr/bin/env python3
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.agent.common import atomic_json,milestone,read_json
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--milestone",required=True);p.add_argument("--phase",required=True);p.add_argument("--state",choices=["current","completed","blocked"],required=True);a=p.parse_args();milestone(a.milestone);s=read_json("docs/workplans/status.json")
 if a.milestone!=s["current_milestone"]: raise SystemExit("Only the current milestone may be updated")
 known=set(s["remaining_phases"]+s["completed_phases"]+[s["current_phase"]])
 if a.phase not in known: raise SystemExit("Unknown phase")
 if a.state=="completed":
  if a.phase not in s["completed_phases"]:s["completed_phases"].append(a.phase)
  s["remaining_phases"]=[x for x in s["remaining_phases"] if x!=a.phase]
 elif a.state=="current":s["current_phase"]=a.phase
 else:s["known_blockers"]=[f"Phase {a.phase} is blocked"]
 atomic_json("docs/workplans/status.json",s)
