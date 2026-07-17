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
- Returned `repository-bootstrap` candidate `2f705f561fe2796f2c98866de41bdd571aa95c93`: its three-test focused suite and diff check pass, and the implementation remains local-Git-only, but the candidate has no `pyproject.toml` or `src/` package layout. The test inserts the package root into `sys.path`, masking that canonical Wave-9 composition cannot import the package through its declared `.../src` path.

### Corrected-candidate re-review

- Returned blueprint correction `ed33fbf88f15f30ace1bbd097c1cf73bb5220cb6` despite its passing three-test focused suite. Normalized path-component comparison now rejects exact duplicates and ancestor/descendant overlap in either direction, preserves similar textual prefixes as disjoint, and prevents integration-owned paths from subsuming specialist paths. Only owned paths changed. However, the commit modifies files introduced by the superseded candidate and cannot be applied alone; its handoff names the replacement only as `HEAD`.
- Returned repository-bootstrap correction `5f368ac96fd1c4cf933ef9ce66213f0dae888016` despite its passing three-test focused suite, canonical import, and package-source compileall. Its `pyproject.toml`, `src/` package, imports, minimal dependencies, local-Git-only behavior, and owned-path diff are correct. However, the commit renames and edits files introduced by superseded `2f705f5`, so applying only this exact SHA is impossible; its handoff also names the replacement only as `HEAD`.
- Neither superseded candidate was accepted or integrated. Each lane must provide a standalone replacement commit from an approved base and a subsequent handoff that records that immutable replacement SHA.

### Recovered standalone replacements — 2026-07-18

- Accepted and integrated `blueprint-compiler` standalone implementation `132207d2814417c4ff187a9703b2770dcdb436a6` as `5d87eb7`; its documentation-only handoff `476cd42` names that exact implementation SHA.
- Accepted and integrated `repository-bootstrap` standalone implementation `6a68fe92e7280d49a9de266cd0baca6ffcdf7c9c` as `9ada09e`; its documentation-only handoff `6ec0456` names that exact implementation SHA.
- Both replacements have owned-path diffs and focused validation. The repository-bootstrap suite passes through the canonical Wave-9 Makefile environment, whose `WAVE09_PYTHONPATH` includes `packages/servicefabric_application_factory_bootstrap/src`; its earlier plain `unittest` import failure was caused by the package source root not being installed or present in that active environment, not by the accepted candidate. No test-side import manipulation was retained.
- The superseded candidates remain unaccepted and unintegrated. Downstream review proceeds with `candidate-review`, `application-integration`, and `evaluation`, followed by the defined pre-Order-12 readiness process.

## Rollback

Revert this integration-only freeze record and boundary verifier; no provider, repository, or application state was changed.
