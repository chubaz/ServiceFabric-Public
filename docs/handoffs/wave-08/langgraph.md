# Wave-8 LangGraph orchestration handoff

- Task: `langgraph`
- Branch: `agent/w8-langgraph`
- Base: `507027eced0bce38114d3db64a77e061017736cc`
- Candidate: `7185397af48b32a780258ed27f1990b97adf2b52` (`feat(langgraph): add provider request plan compiler`)

## Scope

Added `servicefabric_langgraph_orchestration`, a data-only compiler from shared
`AgentRunPlan` and `ProviderPolicy` contracts to dependency-safe batches of
shared `ProviderExecutionRequest` values. It validates missing dependencies and
cycles, honours total and per-provider concurrency limits, and renders task
constraints into canonical request prompts. It does not import provider-runtime
internals, start processes, or call a provider.

## Validation

- `/home/lorenzoccasoni/servicefabric-agent-state/wave-08/langgraph/.venv/bin/python -m unittest discover -s tests/langgraph_orchestration -v` — passed (3 tests)
- `git diff --check` — passed

## Contract changes

None. The implementation consumes only the frozen shared agent and provider
contract packages.

## Deviations and blockers

The manifest's bare `python3` resolves to a system interpreter without
`pydantic`; the same focused command passed using this lane's provisioned
virtual environment. No provider calls were made.

## Rollback

Revert `7185397af48b32a780258ed27f1990b97adf2b52` and the handoff commit. No
external or persistent runtime state was created.

## Next action

Integration can compose these request batches with the provider-runtime lane;
execution remains owned by that runtime.
