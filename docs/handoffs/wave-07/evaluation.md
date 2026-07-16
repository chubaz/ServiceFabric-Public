# Wave-7 task handoff

- Task: `evaluation`
- Commit: `test(wave-07): align evaluation with accepted harness task pack`
- Validation: after `source .agent-runtime.env`, `python3 -m unittest discover -s tests/wave_07 -v` — 3 tests passed
- Blockers: None. The corrected evaluation accepts the three-field `prepare_task` payload and pins the rendered prompt fixture without touching shared contracts or harness code.
- Rollback: `git revert HEAD`
