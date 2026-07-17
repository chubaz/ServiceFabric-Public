# Wave-8 integration handoff

- Task: integration bootstrap and Wave-8 contract freeze.
- Commit: no candidate commits accepted; all specialist lanes remain at the
  Wave-8 bootstrap head.
- Validation: `wave_task_preflight`, Wave-8 boundary checks, provider-contract
  tests, bootstrap tests, and the Wave-7 framework journey passed using the
  lane virtual environment. `make verify-current` and `git diff --check`
  passed. No provider call occurred. `make verify-wave-08` is blocked only at
  its `pip check`: the lane environment has editable Wave-8 packages but does
  not install their Wave-7 dependencies as distributions.
- Blockers: provider runtime, LangGraph orchestration, Pi, Codex, Claude,
  Gemini, and evaluation candidates have not been delivered. Their owned
  paths remain untouched. `contractsStatus: frozen` is recorded in the Wave-8
  control state.
- Rollback: remove the Wave-8 integration bootstrap only; do not alter the
  frozen Wave-7 contracts or any specialist-owned path.

## Candidate review

| Lane | Candidate | Decision | Integration |
| --- | --- | --- | --- |
| provider-runtime | `bef2e16` | accepted; owns the sole subprocess and cancellation implementation | `3facb3f` |
| pi | `b7162d6` | accepted; argv/event/result translation only | `65fac53` |
| codex | `b7b40e6` | accepted; argv/event/result translation only | `0e26c86` |
| claude | `e9aaeab` | accepted; argv/event/result translation only | `18321b7` |
| gemini | `3dadd52`, `a5d2528` | accepted after its provider ID was corrected to `gemini` | `a26b7e5`, `a1a4b32` |
| langgraph | `f007c34` | accepted replacement; consumes the Wave-7 task pack, reads `FileRunStore`, and delegates readiness to `ready_tasks` | `739a568` |

Focused tests passed for every accepted candidate. No provider call occurred.
Evaluation remains deferred.
