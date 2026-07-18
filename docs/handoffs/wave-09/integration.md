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

`make verify-wave-09` passes after specialist integration and final factory composition.

## Candidate review — 2026-07-17

- Accepted `technology-profile` candidate `25a80c9f658059f25de8c15bb765e4ccb3d7abcc`: canonical handoff, full owned-path diff, frozen-boundary inspection, and its five-test focused suite passed. Integrated as `4075ff13a5655b447461e9934e616912b92a1576`.
- Accepted `factory-lifecycle` candidate `91e7c08aa11b9f68bda8c77bd8b302274dd670ee`: canonical handoff, full owned-path diff, factory-only store boundary inspection, and its four-test focused suite passed. Integrated as `dbfa25b4dab2ed6b8fed7ea39e84545c848ab5cf`.
- Returned `blueprint-compiler` candidate `a7235a2ccbf24e8b957d02aa915eb83161caea72`: its lane validation detects only identical allowed paths, not parent/child overlaps. It must enforce hierarchical disjointness before focused verification and acceptance.
- Returned `repository-bootstrap` candidate `2f705f561fe2796f2c98866de41bdd571aa95c93`: its three-test focused suite and diff check pass, and the implementation remains local-Git-only, but the candidate has no `pyproject.toml` or `src/` package layout. The test inserts the package root into `sys.path`, masking that canonical Wave-9 composition cannot import the package through its declared `.../src` path.

### Corrected-candidate re-review

- Returned blueprint correction `ed33fbf88f15f30ace1bbd097c1cf73bb5220cb6` despite its passing three-test focused suite. Normalized path-component comparison now rejects exact duplicates and ancestor/descendant overlap in either direction, preserves similar textual prefixes as disjoint, and prevents integration-owned paths from subsuming specialist paths. Only owned paths changed. However, the commit modifies files introduced by the superseded candidate and cannot be applied alone; its handoff did not record an exact replacement SHA.
- Returned repository-bootstrap correction `5f368ac96fd1c4cf933ef9ce66213f0dae888016` despite its passing three-test focused suite, canonical import, and package-source compileall. Its `pyproject.toml`, `src/` package, imports, minimal dependencies, local-Git-only behavior, and owned-path diff are correct. However, the commit renames and edits files introduced by superseded `2f705f561fe2796f2c98866de41bdd571aa95c93`, so applying only this exact SHA is impossible; its handoff also did not record an exact replacement SHA.
- Neither superseded candidate was accepted or integrated. Each lane must provide a standalone replacement commit from an approved base and a subsequent handoff that records that immutable replacement SHA.

### Recovered standalone replacements — 2026-07-18

- Accepted and integrated `blueprint-compiler` standalone implementation `132207d2814417c4ff187a9703b2770dcdb436a6` as `5d87eb7694adeae9cd402b1968db163d7fac1955`; its documentation-only handoff `476cd42a9202c7a082aca518b79479de8777dacb` names that exact implementation SHA.
- Accepted and integrated `repository-bootstrap` standalone implementation `6a68fe92e7280d49a9de266cd0baca6ffcdf7c9c` as `9ada09eb8358a46ec90f3db804f96f2083ca4fb5`; its documentation-only handoff `6ec045643cbf8fa0c6740231ba8b6866c519831f` names that exact implementation SHA.
- Both replacements have owned-path diffs and focused validation. The repository-bootstrap suite passes through the canonical Wave-9 Makefile environment, whose `WAVE09_PYTHONPATH` includes `packages/servicefabric_application_factory_bootstrap/src`; its earlier plain `unittest` import failure was caused by the package source root not being installed or present in that active environment, not by the accepted candidate. No test-side import manipulation was retained.
- The superseded candidates remain unaccepted and unintegrated. Downstream review proceeds with `candidate-review`, `application-integration`, and `evaluation`, followed by the defined pre-Order-12 readiness process.

### Downstream safety corrections — 2026-07-18

- Accepted `candidate-review` replacement `66136e680270e620f278c9960c6291d8a2318eee` as `c80734165dbe527f93e101dabb2b4a6d3caf88ad`, followed by documentation-only handoff `da97620135a3dccae1a35554be4efd3129b7f490`. Superseded `fa33c0b2216d559bbff8234ee2300002ff8a361f` remains unintegrated.
- Accepted `application-integration` replacement `f755ecf0b550e72c8eb84a737ae643dfaccd22bf` as `718232e926059e98fe017af656334601adb4bda0`, followed by documentation-only handoff `89deb6a6e086f7dbb63a7a0a064ac0e4192e6fa0`. Superseded `6076a55d73db97102ee1c1c9232d765582cd845f` and `f9c3efecc1ea700aebb8835837d8fddcc08143d3` remain unintegrated.
- Candidate-review focused verification passed 6 tests; application-integration focused verification passed 5 tests; both package compile checks and `git diff --check` passed after integration.

### Implementation readiness — 2026-07-18

All six required implementation lanes are accepted and integrated. Their canonical package imports, the frozen Wave-9 boundary verifier, and `git diff --check` pass. Superseded downstream SHAs are not ancestors of this integration branch. Evaluation is a post-composition synchronization task, so the pre-Order-12 gate is passed and Order-12 factory composition may proceed.

### Final evaluation acceptance — 2026-07-18

- Order-12 composition `b5368828d9df5a8c38653be29c4ff85222787f16` and CLI `317a2331b6e23c8f8f09ac455847e2b0fecca24a` supplied the complete public workflow, but their original journey did not satisfy the final evaluation manifest.
- Final journey `7d7195f07ae1b2e0980b022bfe9f9e309b3d9aaf` adds the missing seven-lane, technique-policy, blocked-requirement, subprocess-provider, retry/supersession, candidates/status, and provider-usage-reference coverage.
- Packaging correction `6930121cc57cbd0bf7532d007e5b49c43090a383` installs the declared cumulative Wave-7/8/9 local distributions in one resolver-enabled invocation. A from-scratch isolated environment reports `No broken requirements found.`
- `make verify-wave-09` passed 35 tests plus boundaries, locks, compileall, isolated `pip check`, and `git diff --check`. The subsequent single `make verify-current` run passed.
- No real provider was invoked, no push occurred, and no merge to `main` occurred. The non-authoritative old evaluation changes remain outside integration history.

## Rollback

Revert this integration-only freeze record and boundary verifier; no provider, repository, or application state was changed.
