# Wave-4 Operation-Model Handoff

Lane: operation-model  
Branch: `agent/w4-operation-model`  
Base commit: `8852fd4`  
Candidate commits: `0c21e47`, `495b2b9`, `docs(operation): complete Wave-4 handoff`

## Changed Paths

- `packages/servicefabric_operation_model/**`: immutable `OperationDefinition` and bounded `HttpBinding` records, strict dictionary/file loader, and canonical JSON serialization.
- `schemas/servicefabric/local/v1/operation.schema.json`: draft 2020-12 manifest schema.
- `tests/operation_model/**`: focused contract, rejection, ordering, and round-trip tests.

## Tests Executed

- `python3 -m unittest discover -s tests/operation_model -v` — passed, 4 tests.
- `git diff --check` — passed.

## Contract Changes

The local `OperationDefinition` manifest uses `servicefabric.local/v1` and has a versioned metadata identity, explicit `application_ref`, `module_ref`, and `interface_ref`, and at least one explicit HTTP binding. Bindings support only GET, POST, PUT, PATCH, and DELETE with a relative-safe absolute path. Optional request/response schema references, media types, and a 1–300 second timeout are static metadata only.

The loader rejects unknown fields, malformed references or versions, missing fields, duplicate binding IDs, non-HTTP protocols, unsupported methods, unsafe/query/fragment paths, and invalid timeouts. It sorts bindings by ID and serialization uses compact UTF-8 JSON with sorted keys.

## Decisions and Limitations

- This lane defines static contracts only. It does not invoke operations, resolve interfaces, register definitions, expose capabilities, or implement a transport server or projection.
- References are opaque local identifiers; resolving them belongs to the integration/capability lanes.
- The file loader intentionally accepts JSON only; YAML loading and workspace persistence are outside this lane.

## Blockers

None.

Rollback: revert `495b2b9` and `0c21e47` in reverse order. Do not merge these candidate commits from this lane.
