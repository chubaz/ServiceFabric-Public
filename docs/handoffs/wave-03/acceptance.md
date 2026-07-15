# Wave-3 Lane Handoff

## Lane

`acceptance` on `agent/w3-acceptance`, based on `715de644eff2ee003469f14d574c4b70706bc70a`.

## Candidate commits

- `18197a0 test(wave-03): specify fresh workspace acceptance`

## Scope and ownership check

Added only the owned Wave-3 acceptance fixture and tests. The fixture specifies the fresh external-workspace journey and its required deterministic generation, validation, lifecycle, build, collision, rollback, and cleanup assertions.

## Frozen-contract compliance

No frozen contract, package, service, CLI, schema, or workplan file changed. The acceptance suite is a framework-spanning executable specification; implementation remains owned by the generator, application-builder, and integration lanes.

## Tests and exact results

- `python3 scripts/agent/wave_task_preflight.py --wave wave-03 --task acceptance` — passed.
- `make agent-preflight` — passed.
- `python3 -m unittest discover -s tests/wave_03 -v` — passed (5 tests).
- `git diff --check` — passed.

Machine-readable evidence: `codex/runs/wave-03/acceptance/tests.json` (ignored runtime evidence required by the rendered prompt).

## Known limitations

The specialist branches begin from the Wave-3 bootstrap, before the owned generator, builder, and CLI implementations have been composed. Accordingly, this lane validates the stable acceptance contract rather than invoking not-yet-integrated commands. Integration must execute the fixture's journey against the composed implementation.

## Integration notes

The integration gate should run this suite after the generator, application-builder, and CLI composition is present, and must retain this exact command order:

`workspace init -> apps create -> apps modules -> apps validate -> dev prepare -> dev start -> dev status -> dev restart -> apps build -> dev stop`

No contract change request is needed. Rollback is a revert of the listed candidate commit (and this handoff-only commit); no persistent-data migration is involved.

## Recommendation

Accept the candidate after composition and execute the fresh-workspace journey as part of `make verify-wave-03`.
