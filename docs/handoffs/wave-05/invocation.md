# Wave-5 Task Handoff

Lane: `invocation`
Branch: `agent/w5-invocation`
Base commit: `53f53ca8a4a9a47887902b84a91bc27a812e9483`
Candidate commit: `dd42d66`

## Changed Paths

- `packages/servicefabric_capability_invocation/**`
- `tests/capability_invocation/test_invocation.py`

## Tests Executed

- `source .agent-runtime.env && python3 -m unittest discover -s tests/capability_invocation -v` — passed (4 tests)
- `git diff --check` — passed

## Contracts Consumed

- Static `CapabilityRegistry` and immutable `CapabilityDefinition`
- Reviewed `OperationDefinition` and `HttpBinding`
- Structural ports for derived availability, operation/schema resolution, and transport execution

## Decisions and Limitations

- The service resolves capability → operation → lexically first reviewed binding when no binding ID is supplied, then validates request and response schemas around the adapter call.
- An unavailable capability or missing live endpoint is rejected before any transport call.
- The package is transport-neutral; it contains no HTTP client or route implementation.
- Schema validation supports a bounded declarative JSON Schema subset. Schema references must be resolved by the supplied reviewed schema resolver.

## Blockers

None.

## Rollback

Revert `dd42d66` to remove the isolated invocation package and its focused tests.
