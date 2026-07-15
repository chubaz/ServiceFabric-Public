# Wave-5 Task Handoff

Lane: availability
Branch: agent/w5-availability
Base commit: 53f53ca8a4a9a47887902b84a91bc27a812e9483
Candidate commit: be6b6bf8de2bed5d3d429394611bc974fb83391f

## Changed Paths

- `packages/servicefabric_capability_runtime/**`
- `tests/capability_runtime/test_availability.py`
- `docs/handoffs/wave-05/availability.md`

## Tests Executed

- `PYTHONPATH=packages/servicefabric_capability_runtime/src python3 -m unittest discover -s tests/capability_runtime -v` — passed (3 tests).
- `git diff --check` — passed.

Machine-readable evidence: `.agent-runs/wave-05/availability/tests.json`.

## Contracts Consumed

None. The package accepts reviewed capability owner identities and a bounded
`ModuleHealthSource` protocol; it does not read or modify the frozen static
registry, capability model, operation model, or process runtime.

## Decisions and Limitations

Only a `running` module with health value `healthy` resolves as `available`.
Absent, starting, stopped, failed, and unhealthy observations resolve to a
stable `unavailable` reason. Snapshot serialization is optional, canonical,
and excludes endpoints, process identifiers, credentials, and diagnostics.
Application-status bridging and invocation remain integration and invocation
lane responsibilities.

## Blockers

None.

## Rollback

Revert candidate commit `be6b6bf8de2bed5d3d429394611bc974fb83391f`.
