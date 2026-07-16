# Wave-7 ownership

The seven specialist lanes own the paths named in the Wave-7 bootstrap request. Integration owns shared contracts, CLI, locks, Makefile, CI, composition and metadata.

The specialist path sets are pairwise disjoint:

- `context`: `packages/servicefabric_agentic_context`, `tests/agentic_context`, and its canonical handoff.
- `planner`: `packages/servicefabric_agentic_planner`, `tests/agentic_planner`, and its canonical handoff.
- `run-store`: `packages/servicefabric_agentic_run_store`, `tests/agentic_run_store`, and its canonical handoff.
- `agent-tools`: `packages/servicefabric_agent_tools`, `tests/agent_tools`, and its canonical handoff.
- `orchestrator`: `packages/servicefabric_agentic_orchestrator`, `tests/agentic_orchestrator`, and its canonical handoff.
- `harness`: `packages/servicefabric_agent_harness`, `tests/agent_harness`, and its canonical handoff.
- `evaluation`: `tests/wave_07`, `tests/fixtures/wave_07`, and its canonical handoff.

Each specialist manifest retains a ceiling of one focused test command. Cross-lane and regression verification belongs to integration.
