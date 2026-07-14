# Wave-2 Verification

The canonical gate is `make verify-wave-02`. Completion requires:

- `servicefabric apps dev prepare research-notes`;
- `servicefabric apps dev start research-notes` and aggregate module/resource status;
- note creation and search;
- API-only restart with SQLite data preserved and unrelated modules left running;
- ordered stop with no stale process records, locks, ports, or temporary runtime state;
- AP-00C and Wave-1 regressions.

Before lane work, use `python3 scripts/agent/wave_task_preflight.py --wave wave-02 --task LANE`. Candidate completion uses the corresponding `--wave wave-02` completion checker and canonical handoff.

After finalization, launch prompts with:

```bash
scripts/agents/launch_lane.sh --wave wave-02 integration --interactive
scripts/agents/launch_lane.sh --wave wave-02 supervisor --interactive
scripts/agents/launch_lane.sh --wave wave-02 runtime-bindings --interactive
scripts/agents/launch_lane.sh --wave wave-02 kit-execution --interactive
scripts/agents/launch_lane.sh --wave wave-02 reference-app --interactive
```
