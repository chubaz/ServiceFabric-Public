# Wave-7 integration handoff

- Task: Compose the accepted Wave-7 framework through public APIs and expose the provider-neutral CLI workflow.
- Commits: `72c3a2f` (`feat(integration): compose agentic application framework`) and `8debb14` (`feat(cli): expose agentic application workflow`).
- Validation: the latest evaluation candidate passed `python3 -m unittest discover -s tests/wave_07 -v` with one black-box journey. The minimal `make verify-wave-07` gate is finalized but has not been run for completion.
- Blockers: final integration verification remains pending. `contractsStatus: frozen`; accepted specialist implementations and contracts remain unchanged. Pi, LangGraph, external provider SDKs, and automatic Codex invocation remain deferred.
- Rollback: revert the two composition commits. Existing task worktrees are never deleted automatically; no persistent-data migration is involved.

## Candidate review

`contractsStatus: frozen` remains in force. Candidate review is complete; Wave-7 completion integration remains pending.

### Accepted and integrated

- Context candidate `d9bc15656fb6013ad9f54485913016c8f98f3ac3`; integrated through `87c0af2cfdb41b0bb952bb9c9022197e58f0b486`. Its four focused tests passed. The complete diff is lane-owned, bounded, deterministic, and contains no planning behavior.
- Run-store candidate `4ce57096a242bb6e47ee37d01e78487e8be0f10b`; integrated through `79128e184752bd586263994642b639e53725f81e`. Its seven focused tests passed with the recorded Wave-7 source roots. The complete diff is lane-owned and provides durable atomic storage without scheduling.
- Agent-tools candidate `cf5e98a7544a555720661c09280f44b7b91e4b31`; integrated through `d67470d87f75dff00cc287f93de1d84e06e26d33`. Its twelve focused tests passed. The complete diff is lane-owned and exposes only bounded inspection and injected public-facade discovery; no shell, write, registry, runtime, or provider tool exists.
- Planner candidate `1767aa4d8e10e2f81437cb0af4236d7b03971afa`; integrated through `8b29009e03c0ab532fafbea1c5c0c19ec7d68c87`. Its eight focused tests passed. The complete diff is lane-owned and validates immutable task graphs without persistence or execution.
- Harness candidate `5d1249828705f5235989db3220be783887f815fd`; integrated through `c239e2e630a72a420996eece8ebd89678d4b4286`. Its six focused tests passed. The complete diff is lane-owned and renders and tracks task contracts without planning or invoking a provider.
- Orchestrator candidate `4774d319b5f3c209ddda59ae928e38ed33802277`; integrated through `d98775e7ee656259edd881d9021efcd82b9092be`. Its six focused tests passed. The complete diff is lane-owned and computes dependency readiness without model invocation, file editing, or persistence.
- Evaluation candidate `9eb3a71cc365300c7279f3a2210a8cdec01cd724`; fast-forwarded through the same commit. Its single black-box journey passed in the candidate worktree. The effective delta is limited to `tests/wave_07/**`, `tests/fixtures/wave_07/**`, and `docs/handoffs/wave-07/evaluation.md`; it changes no implementation, frozen contract, or integration control.

No accepted candidate changed `packages/servicefabric_agentic_contracts` or another specialist's path set.

### Returned and superseded

- Evaluation candidate `c4abcd8ed0de4b3c39e1a9b623f915196fedbfec` was returned because its journey enforced the obsolete task-pack shape. Corrected candidate `3a410176207515d55bb93b5ddd8ff4c567a2675f` supersedes it and accepts the integrated harness without implementation changes.

### Direct dependency checks

- The existing Wave-7 evaluation journey passed after planner integration.
- The existing Wave-7 evaluation journey passed again after orchestrator integration.
- The corrected Wave-7 evaluation journey passed after all framework candidates were integrated.

### Next action

Run the finalized minimal `make verify-wave-07` gate and review its result. Do not mark Wave 7 complete yet.
