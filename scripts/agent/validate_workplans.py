#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.agent.common import ROOT,milestones,read_json,safe_path
def validate():
 items=milestones(); ids=[x["id"] for x in items]
 if len(ids)!=len(set(ids)): raise ValueError("duplicate milestone")
 current=[x for x in items if x["status"]=="current"]
 if len(current)!=1: raise ValueError("exactly one milestone must be current")
 status=read_json("docs/workplans/status.json")
 if status["current_milestone"]!=current[0]["id"]: raise ValueError("status and milestone current values differ")
 if current[0]["id"] not in (ROOT/"docs/workplans/current.md").read_text(): raise ValueError("current.md does not name current milestone")
 for item in items:
  safe_path(item["workplan"])
  if not safe_path(item["workplan"]).is_file(): raise ValueError("workplan missing")
  for key in ("required_files","allowed_paths","forbidden_paths"): [safe_path(p) for p in item[key]]
  if set(item["allowed_paths"]) & set(item["forbidden_paths"]): raise ValueError("allowed/forbidden overlap")
  for phases in item["verification"].values():
   for check in phases:
    if not isinstance(check["command"],list): raise ValueError("verification commands must be arrays")
 return True
if __name__=="__main__":
 try: validate(); print("Agent workplans are valid.")
 except Exception as exc: print(f"Agent workplan validation failed: {exc}",file=sys.stderr); raise SystemExit(1)
