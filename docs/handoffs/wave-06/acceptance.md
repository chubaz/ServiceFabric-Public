# Wave-6 Acceptance Handoff

Lane: `acceptance`

## Candidate Scope

- `tests/wave_06/test_capability_consumer_facade.py`
- `docs/handoffs/wave-06/acceptance.md`

The single end-to-end journey creates a temporary Research Notes workspace, registers and starts the application, and verifies the same `notes.search` canonical result through MCP, loopback REST, `CapabilityClient`, and the internal-agent adapter.

## Coverage

- Static `notes.create`, `notes.get`, and `notes.search` registrations persist before and after shutdown.
- MCP exposes `notes.create` and `notes.search`, creates a note, and finds it again.
- REST, Python client, and internal-agent invocation return the same canonical search result; the agent reference uses `notes.search`.
- Stopping `notes-api` makes MCP, REST, Python client, and agent availability unavailable without removing static definitions.
- The existing AP-01A `math.calculate` MCP tool remains discoverable.

## Validation

- `make verify-wave-06`
- `make verify-current`
- `make agent-handoff`

## Limitations

The REST portion uses the bounded literal-loopback test server. It verifies the projection contract, not remote hosting or authentication.

## Rollback

Revert this candidate commit to remove the Wave-6 acceptance journey and its handoff only.
