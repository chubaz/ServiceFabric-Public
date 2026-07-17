# Wave-9 integration contract freeze

`contractsStatus: frozen` is recorded before specialist work.

## Frozen boundaries

- Waves 3, 7, and 8 remain the authoritative generator/blueprint, agentic-contract, and provider-execution surfaces.
- Technology profiles remain governance and planning data; `EngineeringBlueprint` compiles to `AgentRunPlan`.
- Bootstrap does not invoke providers; candidate review is read-only; application integration accepts only reviewed exact commit SHAs.
- No lane may merge to `main`; `UnmetRequirement` records a need without modifying ServiceFabric.
- The seven specialist path sets are disjoint and each retains its two-command focused-test ceiling.

## Validation

- `make agent-preflight` — passed.
- `make verify-current` — passed.
- `integration/phase25-wave9/verify_boundaries.py` — passed.
- `git diff --check` — passed.

`make verify-wave-09` remains pending specialist delivery: it stops at the absent specialist-owned `tests/technology_profiles` suite. No specialist-owned paths were created or modified.

## Candidate review — 2026-07-17

- Accepted `technology-profile` candidate `25a80c9f658059f25de8c15bb765e4ccb3d7abcc`: canonical handoff, full owned-path diff, frozen-boundary inspection, and its five-test focused suite passed. Integrated as `4075ff13a5655b447461e9934e616912b92a1576`.
- Accepted `factory-lifecycle` candidate `91e7c08aa11b9f68bda8c77bd8b302274dd670ee`: canonical handoff, full owned-path diff, factory-only store boundary inspection, and its four-test focused suite passed. Integrated as `dbfa25b4dab2ed6b8fed7ea39e84545c848ab5cf`.
- Returned `blueprint-compiler` candidate `a7235a2`: its lane validation detects only identical allowed paths, not parent/child overlaps. It must enforce hierarchical disjointness before focused verification and acceptance.

## Rollback

Revert this integration-only freeze record and boundary verifier; no provider, repository, or application state was changed.
