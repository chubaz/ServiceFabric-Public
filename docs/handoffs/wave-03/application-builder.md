# Wave-3 Application-Builder Handoff

## Lane

`application-builder`

## Candidate commits

- `47355e1b314fa2d902cb5377b64c3ca66049cb4f` — deterministic multi-module build coordination and focused tests.

## Scope and ownership check

Only `packages/servicefabric_application_builder/**`, `tests/application_builder/**`, and this handoff were changed. No other lane was merged or modified.

## Frozen-contract compliance

The coordinator consumes the existing application assembly, reviewed framework-kit catalog, and artifact-store `put_artifact` API. It introduces no contract changes and does not execute framework commands.

## Tests and exact results

- `PYTHONPATH='packages/servicefabric_application_builder:packages/servicefabric_application_model:packages/servicefabric_application_assembly:packages/servicefabric_framework_kits' python3 -m unittest discover -s tests/application_builder -v` — passed (4 tests).
- `git diff --check` — passed.
- `make verify-current` — passed.
- `make verify-wave-03` — unavailable in this specialist worktree; it is an integration-only gate.
- `python3 scripts/agent/wave_completion.py --wave wave-03` — blocked as expected before other lanes are accepted and integrated.

Machine-readable evidence: `codex/runs/wave-03/application-builder/tests.json`.

## Known limitations

The package deliberately plans and records build outputs but does not execute build commands. A future execution owner must consume the reviewed plans without bypassing this manifest or the artifact-store boundary.

## Integration notes

Integration can install `servicefabric-application-builder` alongside the existing reviewed packages, invoke `ApplicationBuildCoordinator.plan(...)`, then create a manifest from executor-produced output roots. `publish_artifact(...)` delegates to the existing immutable artifact store.

## Recommendation

Accept `47355e1b314fa2d902cb5377b64c3ca66049cb4f` after normal integration review, then run the canonical Wave-3 gate from the integration worktree.
