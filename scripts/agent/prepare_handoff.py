#!/usr/bin/env python3
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.agent.common import ROOT,git,read_json
PROMPT="Read AGENTS.md and docs/workplans/current.md. Run make agent-preflight. Implement the current milestone only. Run make verify-current and make agent-handoff. Report blockers, deviations, limitations, validation, and rollback."
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--milestone",required=True);a=p.parse_args();s=read_json("docs/workplans/status.json");out=ROOT/".agent/handoff.md";out.parent.mkdir(exist_ok=True)
 text=f"# Agent handoff\n\nMilestone: {a.milestone}\nBranch: {git('branch','--show-current').stdout.strip() or 'detached'}\nBase: {s['base_commit']}\nHead: {git('rev-parse','HEAD').stdout.strip()}\nCurrent phase: {s['current_phase']}\nCompleted phases: {', '.join(s['completed_phases']) or 'none'}\nKnown blockers: {', '.join(s['known_blockers']) or 'none'}\nLast verification: {s['last_verification_summary']}\nNext action: {s['next_action']}\n\n{PROMPT}\n";out.write_text(text,encoding="utf-8");print(out.relative_to(ROOT))
