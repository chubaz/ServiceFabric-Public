# Wave-6 Task Handoff

Lane: `mcp-projection`
Branch: `agent/w6-mcp-projection`
Base commit: `9b40277fc648e1673a98d32f49ed2d444d632dd3`
Candidate commit: `fix(mcp): delegate capability projection through consumer facade`

## Changed Paths

- `packages/servicefabric_capability_mcp_projection/**`
- `tests/capability_mcp_projection/**`
- `docs/handoffs/wave-06/mcp-projection.md`

## Tests Executed

- Wave-6 Python environment: `python3 -m unittest discover -s tests/capability_mcp_projection -v` — passed, 3 tests.
- `git diff --check` — passed.

Evidence: `.agent-runs/wave-06/mcp-projection/tests.json`.

## Contracts Consumed

- `CapabilityConsumerFacade.list_capabilities(application_id)` supplies registered candidate identity and descriptive metadata.
- `CapabilityConsumerFacade.availability_for_application(application_id)` supplies the derived visibility view.
- `CapabilityConsumerFacade.invoke_capability(capability_id, input_value)` remains the only call execution path.

## Decisions and Limitations

- MCP names equal canonical capability IDs, preserving stable identity without a second naming registry.
- Registered unavailable capabilities remain candidates with a stable unavailability reason; consumer discovery may filter on `available`.
- The projection advertises only a permissive object input shape. Canonical runtime schema validation remains authoritative.
- MCP consumes the integration-owned `CapabilityConsumerFacade`; it neither accesses `CapabilityRegistry` nor constructs `CapabilityRuntimeService`.
- Existing AP-01A MCP tools and gateway behavior are unchanged.
- No endpoint resolution, transport, application business logic, authentication, or automatic publication was added.

## Blockers

None.

## Rollback

Revert the correction commit; it has no persisted-data migration.
