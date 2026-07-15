# Wave-6 Task Handoff

Lane: `mcp-projection`
Branch: `agent/w6-mcp-projection`
Base commit: `9b40277fc648e1673a98d32f49ed2d444d632dd3`
Candidate commit: `58fc05c`

## Changed Paths

- `packages/servicefabric_capability_mcp_projection/**`
- `tests/capability_mcp_projection/**`
- `docs/handoffs/wave-06/mcp-projection.md`

## Tests Executed

- `PATH=/tmp/servicefabric-ap-01a/bin:$PATH python3 -m unittest discover -s tests/capability_mcp_projection -v` — passed, 3 tests.
- `git diff --check` — passed.
- `git diff --cached --check` — passed before the candidate commit.

Evidence: `.agent-runs/wave-06/mcp-projection/tests.json`.

## Contracts Consumed

- `CapabilityRegistry.list_capabilities(application_id)` is the sole source of explicitly registered candidates.
- `CapabilityDefinition` supplies stable identity, title, and objective metadata without alteration.
- `CapabilityRuntimeService.availability(capability_id)` supplies the derived availability view.
- `CapabilityRuntimeService.invoke(capability_id, input_value)` remains the only call execution path.

## Decisions and Limitations

- MCP names equal canonical capability IDs, preserving stable identity without a second naming registry.
- Registered unavailable capabilities remain candidates with a stable unavailability reason; consumer discovery may filter on `available`.
- The projection advertises only a permissive object input shape. Canonical runtime schema validation remains authoritative.
- The package uses structural runtime interfaces so integration owns composition with the Python `CapabilityRuntimeService` and existing MCP gateway.
- No endpoint resolution, transport, application business logic, authentication, or automatic publication was added.

## Blockers

None.

## Rollback

Revert candidate commit `58fc05c`; it is additive and has no persisted-data migration.
