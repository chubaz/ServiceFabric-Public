# Wave-7 integration handoff

- Task: Freeze the Wave-7 contract seed and integration boundaries.
- Commit: integration freeze candidate (this commit).
- Validation: `make verify-wave-07`, `make verify-current`, and `git diff --check` passed; the integration gate enforces the frozen boundary record, seven pairwise-disjoint specialist path sets, and a one-command focused-test ceiling per specialist.
- Blockers: none. `contractsStatus: frozen`; specialist-owned behavior remains untouched. Pi, LangGraph, and provider adapters remain deferred to Wave 8.
- Rollback: revert the integration metadata and documentation commit; no persistent-data migration is involved.

## Candidate review

`contractsStatus: frozen` remains in force. This review does not perform Wave-7 completion integration or run the full-wave verification gates.

### Accepted and integrated

- Context candidate `d9bc15656fb6013ad9f54485913016c8f98f3ac3`; integrated through `87c0af2cfdb41b0bb952bb9c9022197e58f0b486`. Its four focused tests passed. The complete diff is lane-owned, bounded, deterministic, and contains no planning behavior.
- Run-store candidate `4ce57096a242bb6e47ee37d01e78487e8be0f10b`; integrated through `79128e184752bd586263994642b639e53725f81e`. Its seven focused tests passed with the recorded Wave-7 source roots. The complete diff is lane-owned and provides durable atomic storage without scheduling.
- Agent-tools candidate `cf5e98a7544a555720661c09280f44b7b91e4b31`; integrated through `d67470d87f75dff00cc287f93de1d84e06e26d33`. Its twelve focused tests passed. The complete diff is lane-owned and exposes only bounded inspection and injected public-facade discovery; no shell, write, registry, runtime, or provider tool exists.
- Planner candidate `1767aa4d8e10e2f81437cb0af4236d7b03971afa`; integrated through `8b29009e03c0ab532fafbea1c5c0c19ec7d68c87`. Its eight focused tests passed. The complete diff is lane-owned and validates immutable task graphs without persistence or execution.
- Harness candidate `5d1249828705f5235989db3220be783887f815fd`; integrated through `c239e2e630a72a420996eece8ebd89678d4b4286`. Its six focused tests passed. The complete diff is lane-owned and renders and tracks task contracts without planning or invoking a provider.
- Orchestrator candidate `4774d319b5f3c209ddda59ae928e38ed33802277`; integrated through `d98775e7ee656259edd881d9021efcd82b9092be`. Its six focused tests passed. The complete diff is lane-owned and computes dependency readiness without model invocation, file editing, or persistence.

No accepted candidate changed `packages/servicefabric_agentic_contracts` or another specialist's path set.

### Returned

- Evaluation candidate `c4abcd8ed0de4b3c39e1a9b623f915196fedbfec` is path-owned and freeze-clean, and its three focused tests pass on its original branch. It was returned unmerged because its journey asserts the obsolete two-field `CodexPromptHarness.prepare_task` result. The accepted harness now includes the rendered `prompt` in that task pack. The corrected evaluation must assert or otherwise accept that prompt field and pass against the integrated candidates.

### Direct dependency checks

- The existing Wave-7 evaluation journey passed after planner integration.
- The existing Wave-7 evaluation journey passed again after orchestrator integration.

### Next action

Review a corrected evaluation candidate when ready. Do not perform completion integration yet.
