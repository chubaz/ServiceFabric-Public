# Wave-08 Pi lane handoff

## Candidate

- Commit: `b7162d6 feat(pi): add provider harness adapter`
- Scope: `packages/servicefabric_pi_harness` and `tests/pi_harness` only.

## Delivered

- `PiHarnessAdapter`, a structural implementation of the shared `ExecutableHarnessAdapter` boundary.
- Deterministic Pi CLI argv construction, JSON-lines event translation, and shared-contract result recovery.
- No subprocess creation, lifecycle control, credentials, or provider-runtime implementation.

## Validation

- `git diff --check` passed before the candidate commit.
- `python3 -m unittest discover -s tests/pi_harness -v` is blocked before test execution: the available interpreter lacks `pydantic`, required by the frozen `servicefabric_agent_provider_contracts` package.

## Limitations and rollback

- Validation must be rerun in the pinned project runtime with `pydantic` installed.
- Roll back by reverting `b7162d6`; no persistent state or migrations are involved.
