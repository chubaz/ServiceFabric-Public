from __future__ import annotations
import json
import os
from pathlib import Path
from servicefabric_agentic_contracts import AgentHandoff, AgentRunPlan, AgentTaskResult

class FileRunStore:
    def __init__(self, root: str | Path): self.root = Path(root)
    def _path(self, run_id: str) -> Path: return self.root / f"{run_id}.json"
    def save_plan(self, plan: AgentRunPlan) -> None:
        self._write(plan.run_id, {"plan": plan.model_dump(mode="json"), "results": {}})
    def load(self, run_id: str) -> dict:
        return json.loads(self._path(run_id).read_text(encoding="utf-8"))
    def record_result(self, run_id: str, result: AgentTaskResult) -> None:
        state = self.load(run_id); state["results"][result.task_id] = result.model_dump(mode="json"); self._write(run_id, state)
    def handoff(self, run_id: str) -> AgentHandoff:
        state = self.load(run_id); results = tuple(AgentTaskResult.model_validate(v) for _, v in sorted(state["results"].items()))
        statuses = {item.status for item in results}; status = "blocked" if "blocked" in statuses else "failed" if "failed" in statuses else "success" if results and all(x.status == "success" for x in results) else "running"
        blockers = tuple(b for item in results for b in item.blockers)
        return AgentHandoff(run_id=run_id, status=status, task_results=results, unresolved_blockers=blockers)
    def _write(self, run_id: str, value: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True); target = self._path(run_id); temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"); os.replace(temp, target)
