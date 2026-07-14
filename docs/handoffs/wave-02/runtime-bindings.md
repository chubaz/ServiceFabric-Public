# Wave-2 Task Handoff

Lane: runtime-bindings
Branch: agent/w2-runtime-bindings
Base commit: 715de644eff2ee003469f14d574c4b70706bc70a
Head commit: aea040ca22f02f484a97474d91027c7947ffbee9
Worktree: SF_WT_RUNTIME_BINDINGS

## Objective

Implemented application-scoped SQLite, filesystem, and allocated-loopback bindings with durable resolved state, environment projection, idempotent reuse, application-state isolation, and volatile-allocation release.

## Changed Paths

- `packages/servicefabric_resource_bindings/servicefabric_resource_bindings/__init__.py`
- `packages/servicefabric_resource_bindings/servicefabric_resource_bindings/local.py`
- `tests/resource_bindings/test_resource_bindings.py`
- `docs/handoffs/wave-02/runtime-bindings.md`

## Candidate Commits

- `aea040ca22f02f484a97474d91027c7947ffbee9 feat(bindings): persist application local resources`

## Tests Executed

- `python3 -m unittest discover -s tests/resource_bindings -v`
- `git diff --check`

Machine-readable evidence: `.agent-runs/wave-02/runtime-bindings/tests.json`.

## Contract Changes

none

## Deviations

The binding service accepts an application-private state directory from its caller; it does not resolve workspace paths or launch processes. SQLite and filesystem data persist across release, while loopback allocations are marked released and reallocated on the next prepare.

## Blockers

none

## Rollback

Revert `aea040ca22f02f484a97474d91027c7947ffbee9` to remove the local provider without changing frozen contracts, supervisor behavior, or CLI behavior.

## Next Action

The supervisor lane should construct `ApplicationLocalBindings` with its application-private state directory, call `plan()` during prepare, pass `ResourceBindingPlan.environment` to managed modules, and call `release()` during ordered shutdown.
