# Wave-7 integration handoff

- Task: Compose the accepted Wave-7 framework through public APIs and expose the provider-neutral CLI workflow.
- Commits: `72c3a2f` (`feat(integration): compose agentic application framework`) and `8debb14` (`feat(cli): expose agentic application workflow`).
- Final verified HEAD: `4995782ac27bb8b85128abefc286da3a2152a3f7` on `integration/phase25-wave7`.
- Validation: all formal gates passed. `make verify-wave-07` passed frozen-boundary validation, 50 tests across nine suites, and its whitespace check; `make verify-current` passed readiness; a final `git diff --check` passed.
- Blockers: none. `contractsStatus: frozen`; accepted specialist implementations and contracts remain unchanged. Pi, LangGraph, external provider SDKs, and automatic Codex invocation remain deferred.
- Rollback: revert the two composition commits. Existing task worktrees are never deleted automatically; no persistent-data migration is involved.

## Candidate review

`contractsStatus: frozen` remains in force. Candidate review and Wave-7 completion integration are complete.

### Accepted and integrated

- Context candidate `d9bc15656fb6013ad9f54485913016c8f98f3ac3`; integrated through `87c0af2cfdb41b0bb952bb9c9022197e58f0b486`. Its four focused tests passed. The complete diff is lane-owned, bounded, deterministic, and contains no planning behavior.
- Run-store candidate `4ce57096a242bb6e47ee37d01e78487e8be0f10b`; integrated through `79128e184752bd586263994642b639e53725f81e`. Its seven focused tests passed with the recorded Wave-7 source roots. The complete diff is lane-owned and provides durable atomic storage without scheduling.
- Agent-tools candidate `cf5e98a7544a555720661c09280f44b7b91e4b31`; integrated through `d67470d87f75dff00cc287f93de1d84e06e26d33`. Its twelve focused tests passed. The complete diff is lane-owned and exposes only bounded inspection and injected public-facade discovery; no shell, write, registry, runtime, or provider tool exists.
- Planner candidate `1767aa4d8e10e2f81437cb0af4236d7b03971afa`; integrated through `8b29009e03c0ab532fafbea1c5c0c19ec7d68c87`. Its eight focused tests passed. The complete diff is lane-owned and validates immutable task graphs without persistence or execution.
- Harness candidate `5d1249828705f5235989db3220be783887f815fd`; integrated through `c239e2e630a72a420996eece8ebd89678d4b4286`. Its six focused tests passed. The complete diff is lane-owned and renders and tracks task contracts without planning or invoking a provider.
- Orchestrator candidate `4774d319b5f3c209ddda59ae928e38ed33802277`; integrated through `d98775e7ee656259edd881d9021efcd82b9092be`. Its six focused tests passed. The complete diff is lane-owned and computes dependency readiness without model invocation, file editing, or persistence.
- Evaluation candidate `9eb3a71cc365300c7279f3a2210a8cdec01cd724`; fast-forwarded through the same commit. Its single black-box journey passed in the candidate worktree. The effective delta is limited to `tests/wave_07/**`, `tests/fixtures/wave_07/**`, and `docs/handoffs/wave-07/evaluation.md`; it changes no implementation, frozen contract, or integration control.

No accepted candidate changed `packages/servicefabric_agentic_contracts` or another specialist's path set.

## Commit provenance

### Accepted specialist candidates

- Context: `d9bc15656fb6013ad9f54485913016c8f98f3ac3`.
- Planner: `1767aa4d8e10e2f81437cb0af4236d7b03971afa`.
- Run-store: `4ce57096a242bb6e47ee37d01e78487e8be0f10b`.
- Agent-tools: `cf5e98a7544a555720661c09280f44b7b91e4b31`.
- Orchestrator: `4774d319b5f3c209ddda59ae928e38ed33802277`.
- Harness: `5d1249828705f5235989db3220be783887f815fd`.
- Evaluation: `9eb3a71cc365300c7279f3a2210a8cdec01cd724`.

Every specialist lane is accepted and integrated.

### Integration history

The integration first-parent history after base `82e464c7e4a22aab5aa47d71f38e9f1796ea253b`, in order, is:

1. `26dd497b5422b89c02a4524585f3ebb4356a4cba` — bootstrap Wave-7.
2. `78df676fbea484eff762e55118488012802f02e4` — include capability consumers in runtimes.
3. `9f36513f6516015cf314674eedff70b0573a182d` — declare worktree environment.
4. `f0cc2edbc0ba30882cd74f988f898cf0e589e1bb` — freeze integration boundaries.
5. `eb868b84da97fcebe50e54f73fa3f4e30814c343` — enforce boundary freeze.
6. `73b9d698c2abe93fcf7d83722d6cf823e2db32a0`, `87c0af2cfdb41b0bb952bb9c9022197e58f0b486` — integrate context and handoff.
7. `ba2a4b748197935cfc9acc24b2becf5ff8e4b2cb`, `79128e184752bd586263994642b639e53725f81e` — integrate run-store and handoff.
8. `57871a3a8c87611148e71ebaf5116d9c315fac7f`, `d67470d87f75dff00cc287f93de1d84e06e26d33` — integrate agent-tools and handoff.
9. `7a50038b740569ce2cfdde4235c1aaf5625b9662`, `8b29009e03c0ab532fafbea1c5c0c19ec7d68c87` — integrate planner and handoff.
10. `a780ca4f9b21ee717cfe004686d08526d068ee1b`, `c239e2e630a72a420996eece8ebd89678d4b4286` — integrate harness and handoff.
11. `a32cc8634981f03610e222f31a9d1abd1f424a85`, `d98775e7ee656259edd881d9021efcd82b9092be` — integrate orchestrator and handoff.
12. `c769cf4d677e85a1c4c6fcc6bc73e1a8f30f217b` — record candidate review.
13. `f564ce18bd9eb68e01cb511b80bedf4a307ea364` — install Wave-7 packages in runtimes.
14. `cb0395d293d96b1b66400afe53dbcb5273f0a9e7` — clarify the harness task-pack contract.
15. `49894b3a63c2ac1752ba234014b7807367865949`, `baa54ed3c40b0324e9b714b5fffd577a42b03ddf` — merge and accept corrected evaluation.
16. `72c3a2f60cb8c7162ae31eab01b3a27979c30c84` — compose the public agentic APIs.
17. `8debb14640bf4fde5a24cb18912ed466afe2f010` — expose the CLI workflow.
18. `9eb3a71cc365300c7279f3a2210a8cdec01cd724` — integrate the final black-box evaluation.
19. `4995782ac27bb8b85128abefc286da3a2152a3f7` — accept evaluation and finalize the minimal formal gate.

## Exact verification evidence

- `make verify-wave-07` — passed at `4995782ac27bb8b85128abefc286da3a2152a3f7`:
  - frozen boundaries: passed; seven disjoint specialist path sets; focused-test ceiling one;
  - agentic contracts: 2 tests passed;
  - context: 4 tests passed;
  - planner: 8 tests passed;
  - run-store: 7 tests passed;
  - agent-tools: 12 tests passed;
  - orchestrator: 6 tests passed;
  - harness: 6 tests passed;
  - black-box evaluation: 1 test passed;
  - integration composition and CLI: 4 tests passed;
  - target-owned `git diff --check`: passed.
- `make verify-current` — passed current-milestone readiness.
- `git diff --check` — passed independently after the Wave-7 and current gates.

## Accepted contract decisions

- Agentic contracts remain immutable data and protocols; context, planning, storage, orchestration, harness, and tools retain separate ownership boundaries.
- The authoritative `CodexPromptHarness` task pack contains exactly `task_id`, `repository`, and `prompt`. `task` and `instructions` are obsolete evaluation fields.
- Context does not plan; planning does not persist or execute; run storage does not schedule; orchestration does not invoke models or edit files; harnesses do not plan.
- Workspace and application agent operations use existing public services. Capability operations delegate through `CapabilityConsumerFacade`; there is no direct registry/runtime access or arbitrary shell tool.
- Rendering emits the bounded prompt and exact `codex exec` launch command without invoking Codex. Pi, LangGraph, external model-provider SDKs, and provider adapters remain outside Wave 7.

## Known limitations

- Wave 7 has no model-provider execution adapter; it exports provider-neutral task packs and launch commands only.
- Preparation requires a local Git worktree. Existing work is never force-reset, deleted, or automatically cleaned.
- Verification accepts only task-declared commands through the bounded argv boundary; shell interpreters and undeclared commands are rejected.
- Durable run state is local and file-backed. Distributed scheduling and remote state coordination are deferred.

## Rollback order

1. Revert this completion metadata commit.
2. Revert `4995782ac27bb8b85128abefc286da3a2152a3f7`, then `9eb3a71cc365300c7279f3a2210a8cdec01cd724`, to remove final evaluation acceptance.
3. Revert `8debb14640bf4fde5a24cb18912ed466afe2f010`, then `72c3a2f60cb8c7162ae31eab01b3a27979c30c84`, to remove CLI and composition.
4. Revert accepted specialist integrations in reverse dependency order: evaluation, orchestrator, harness, planner, agent-tools, run-store, context.
5. Revert runtime and boundary bootstrap commits last. Do not delete task worktrees automatically.

### Returned and superseded

- Evaluation candidate `c4abcd8ed0de4b3c39e1a9b623f915196fedbfec` was returned because its journey enforced the obsolete task-pack shape. Corrected candidate `3a410176207515d55bb93b5ddd8ff4c567a2675f` supersedes it and accepts the integrated harness without implementation changes.

### Direct dependency checks

- The existing Wave-7 evaluation journey passed after planner integration.
- The existing Wave-7 evaluation journey passed again after orchestrator integration.
- The corrected Wave-7 evaluation journey passed after all framework candidates were integrated.

### Next action

Wave 7 is complete on `integration/phase25-wave7`. A merge into `main` requires a separate explicit integration action.
