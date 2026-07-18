# Wave-09 factory-lifecycle handoff

- Lane: `factory-lifecycle`
- Branch: `agent/w9-factory-lifecycle`
- Candidate commit: `91e7c08aa11b9f68bda8c77bd8b302274dd670ee`
- Status: complete

## Delivered

Added `FileFactoryLifecycleStore`, which atomically persists only factory-owned approvals, candidate-review decisions, unmet requirements, and final handoff references. Records are immutable and idempotent by record ID; conflicting replacements and corrupt or cross-run state are rejected. The store does not persist task plans, task results, provider events, usage, or generic run state.

## Validation

- Passed: Wave-9 focused `tests/application_factory_state` suite — 4 tests.
- Passed: `git diff --check`.
- Evidence: `.agent-runs/wave-09/factory-lifecycle/tests.json`.

## Limitations and deviations

The rendered prompt references `docs/handoffs/wave-09/task-handoff-template.md`, but that file is absent in the bootstrap commit. This handoff uses the prompt-required lane, commit, delivered scope, validation, evidence, and limitation fields directly.

## Rollback

Revert commit `91e7c08aa11b9f68bda8c77bd8b302274dd670ee`; no persistent application data migration is introduced.
