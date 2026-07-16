# Wave-7 task handoff

- Task: `evaluation` — one black-box journey covering intent loading, complete context inventory, deterministic concurrent planning, safe worktrees and task packs, prompt-only Codex rendering, dependency success and failure behavior, durable evidence and resume, deterministic handoff, and Wave-6 facade capability discovery.
- Commit: `test(wave-07): prove complete black-box journey`.
- Validation: `make verify-wave-07` and `make verify-current` passed.
- Blockers: None. The acceptance journey changes only evaluation-owned tests, fixtures, and this handoff; model execution remains outside the harness.
- Rollback: `git revert HEAD`
