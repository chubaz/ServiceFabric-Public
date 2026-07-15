# Wave-6 Integration Handoff

## Projection Candidate Review

`contractsStatus: frozen` remains in force. Acceptance was not launched or reviewed.

### MCP projection — returned

Candidate head: `cf08735ce1d07560d34130ce623d025756599215`.

The three focused tests passed. The candidate was returned without merge because its commits use disallowed lane subjects (`feat(mcp):` and `docs(handoff):`), and the projection injects and calls `CapabilityRegistry` directly. This conflicts with the frozen boundary that projections delegate to `CapabilityRuntimeService` and do not own registry behavior.

### REST projection — returned

Candidate head: `1b847552921336c9b3d671d3bc91504dad01351a`.

The three focused loopback tests passed when executed outside the sandbox socket restriction; the server enforces literal `127.0.0.1` binding. The candidate was returned without merge because its required `list_capabilities` and `describe_capability` runtime operations are absent from the frozen concrete Wave-5 `CapabilityRuntimeService`. Adding them changes a frozen contract; reading the registry in the projection or an adapter violates the direct runtime-delegation boundary.

### Python and agent projection — accepted

Candidate head: `c62aa2bbe103f12c641d60cf818f5b2acaf8f172`; merged by `a530cf7d4fac4347e2dd520c14311c8ccbfad86c`.

The candidate changes only its owned package, tests, and handoff; its three focused tests pass before and after merge. `CapabilityClient` and the immutable internal-agent reference delegate directly to the frozen runtime availability, application-scoped discovery, and invocation APIs. No registry, endpoint, or invocation logic is introduced in consumers.

## Directly Dependent Verification

- MCP focused suite: passed, 3 tests.
- REST focused suite: passed, 3 tests on literal loopback.
- Python and agent focused suite: passed, 3 tests before and after merge.
- `git diff --check`: passed.

## Next Action

Return corrected MCP and REST candidates, then review composition. Acceptance remains blocked pending all three projections and integration composition.

## Rollback

Revert merge `a530cf7d4fac4347e2dd520c14311c8ccbfad86c` to remove the accepted Python and agent projection. No frozen contract changed.
