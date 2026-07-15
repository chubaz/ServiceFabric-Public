# Wave-5 Task Handoff

Lane: availability
Branch: agent/w5-availability
Base commit: 53f53ca8a4a9a47887902b84a91bc27a812e9483
Candidate commits: be6b6bf8de2bed5d3d429394611bc974fb83391f, 8b4a7da74ddec339f6410b769ab6d9d463ff35b4

## Changed Paths

- `packages/servicefabric_capability_runtime/**`
- `tests/capability_runtime/test_availability.py`
- `docs/handoffs/wave-05/availability.md`

## Tests Executed

- `python3 -m unittest discover -s tests/capability_runtime -v` — passed (3 tests).
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

Revert candidate commits `8b4a7da74ddec339f6410b769ab6d9d463ff35b4` and
`be6b6bf8de2bed5d3d429394611bc974fb83391f`, in that order.
