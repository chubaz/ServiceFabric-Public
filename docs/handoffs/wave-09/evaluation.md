# Wave-9 final evaluation handoff

## Immutable integration identities

- Approved Wave-9 bootstrap: `3bf95f971aa73ca5105e14e90e04e4a16511a0b0`
- Implementation readiness: `cca8486300f68ce0bbdb7a4764c32c60e7c455ff`
- Order-12 composition: `b5368828d9df5a8c38653be29c4ff85222787f16`
- Factory CLI: `317a2331b6e23c8f8f09ac455847e2b0fecca24a`
- Final complete journey: `7d7195f07ae1b2e0980b022bfe9f9e309b3d9aaf`
- Deterministic packaging correction: `6930121cc57cbd0bf7532d007e5b49c43090a383`
- Evaluation acceptance: `30a67d7906e2f5ea9b143ecde04031df25adf26c`

## Evaluation decision

The journey originally committed with Order-12 was not sufficient for the final
manifest. It covered planning, explicit approval, basic bootstrap, Wave-8
delegation through an in-memory spy, one accepted candidate, integration, and a
handoff. It did not prove the final seven-lane topology, technique-policy
preservation, the blocked unmet-requirement path, subprocess-backed provider
execution, candidate discovery and status, retry/supersession, or a canonical
provider-usage reference.

The final journey now covers the complete public sequence: plan, approval,
bootstrap, provider execution, candidate discovery, candidate review,
exact-commit integration, status, and final handoff.

| Final requirement | Integration evidence | Result |
|---|---|---|
| Seven deterministic engineering lanes and ownership | Five module lanes plus integration and assurance; exact allowed paths and common approved base asserted | accepted |
| Technique-policy preservation | Exact references asserted in the profile and generated lane `AGENTS.md` guidance | accepted |
| Unresolved required resource | Structured `UnmetRequirement`; no repository, worktrees, bootstrap, execution, or provider call | accepted |
| Wave-8 execution delegation | Real `ProviderExecutionService` and provider runtime execute the bounded local fake process | accepted |
| Normalized events, canonical results, and usage | Seven subprocess tasks, 28 validated provider events, canonical task results, and seven canonical usage records | accepted |
| Immutable candidate identity | Full 40-character commit SHAs are reviewed; a mutable lane reference is rejected | accepted |
| Retry and supersession | Initial candidate is returned, replacement exact SHA becomes current, prior SHA is recorded as superseded, and only latest accepted SHAs integrate | accepted |
| Repository safety | Accepted integration service rejects dirty, divergent, superseded, already-integrated, changed-path-mismatch, wrong-branch, and undeclared-verification states | accepted |
| Provider usage in handoff | `provider-usage:<run-id>` references Wave-8 canonical usage; no event or usage record is copied into factory state | accepted |
| Deterministic status and handoff | Reviews, supersession, usage, blockers, verification, integration identity, and repeated handoff rendering are asserted | accepted |

Application integration runs the verification commands declared by the accepted
EngineeringBlueprint. The generated Python application declares
`python3 -m unittest`; it declares no separate build or bounded development-smoke
command, so no undeclared command is inferred or executed.

## Validation evidence

- Wave-9 boundaries: seven disjoint specialist path sets.
- Factory contracts: 3 passed.
- Technology profiles: 5 passed.
- Engineering blueprints: 3 passed.
- Factory lifecycle: 4 passed.
- Repository bootstrap: 3 passed.
- Candidate review: 6 passed.
- Application integration: 5 passed.
- Final evaluation journey, including the fake executable provider: 3 passed.
- Wave-8 delegation smoke: 1 passed.
- Generator and blueprint smokes: 2 passed.
- Formal `make verify-wave-09`: passed, 35 tests plus boundary, lock, compile, isolated packaging, and diff checks.
- Subsequent single `make verify-current`: passed for `ap-00-modular-framework-kits/readiness`.

## Isolated packaging diagnosis

- Defect classification: correctly declared local dependencies were not installed,
  and the deterministic local-package installation list was incomplete.
- Canonical environment: `/home/lorenzoccasoni/servicefabric-agent-state/wave-09/integration/.venv`.
- Fresh validation environment:
  `/tmp/servicefabric-wave09-fresh-6930121/state/wave-09/integration/.venv`.
- Fresh Python executable:
  `/tmp/servicefabric-wave09-fresh-6930121/state/wave-09/integration/.venv/bin/python`.
- Environment creation used `/usr/bin/python3 -m venv`; system site packages are disabled.
- Setup installed the locked test requirements, locked generated-application
  runtime requirements, and 54 local editable distributions in one
  dependency-resolving invocation without `--no-deps` or `PYTHONPATH`.
- Fresh isolated `python -m pip check`: `No broken requirements found.`

No dependency declaration, distribution name, or lock correction was required.

## Safety and disposition

- No Codex, Claude, Gemini, or Pi provider executable was invoked. Only the local
  Wave-8 fake executable fixture ran.
- No provider output was interpreted as approval.
- No candidate code was changed by review.
- No force, reset, delete, push, or merge to `main` occurred.
- The approved base remains unchanged; integration applies only accepted exact
  commit SHAs to the application integration worktree.
- The old non-authoritative evaluation state was not integrated or reused.
