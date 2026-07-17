# Wave-8 LangGraph orchestration handoff

- Task: `langgraph`
- Branch: `agent/w8-langgraph`
- Base: `507027eced0bce38114d3db64a77e061017736cc`
- Replacement candidate: `f007c34815719c38f10d88bdfc4b414d8e5ac839` (`fix(langgraph): delegate task readiness to Wave-7`)
- Supersedes: `7185397af48b32a780258ed27f1990b97adf2b52`, returned for boundary review

## Scope

The LangGraph lane now reads authoritative task results from `FileRunStore`,
validates them as `AgentTaskResult` values, and delegates readiness entirely to
the public Wave-7 `ready_tasks` API. For each ready task only, it obtains the
authoritative `{task_id, repository, prompt}` task pack from
`CodexPromptHarness.prepare_task`, selects a provider through `ProviderPolicy`,
and constructs a bounded `ProviderExecutionRequest`.

No task prompt rendering, dependency traversal, task-state persistence,
provider runtime import, subprocess handling, provider invocation, or provider
SDK logic is present. Batching applies only the policy's per-provider limit to
the already-ready request set.

## Validation

- `PATH=/home/lorenzoccasoni/servicefabric-agent-state/wave-08/langgraph/.venv/bin:$PATH python3 -m unittest discover -s tests/langgraph_orchestration -v` — passed (2 tests)
- `git diff --check` — passed

The focused tests prove canonical task-pack prompt propagation through the
frozen `ProviderExecutionRequest` whitespace normalization, persisted
completed/pending/running state handling via `ready_tasks`, no `FileRunStore`
mutation, and provider-policy batching of ready tasks only.

## Contract changes

None. Wave-7 and shared provider contracts remain unchanged.

## Rollback

Revert `f007c34815719c38f10d88bdfc4b414d8e5ac839` and the handoff update. No
provider or persistent runtime state is created by this lane.

## Next action

Integration may compose the ready request batches with the provider-runtime
lane; execution remains exclusively runtime-owned.
