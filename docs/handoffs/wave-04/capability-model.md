# wave-04 capability-model Handoff

## Scope completed

- Added `CapabilityDefinition`, `CapabilityDefinitionSpec`, and `CapabilityMetadata` in `packages/servicefabric_capability_model`.
- Capability declarations are strict and immutable, use `servicefabric.local/v1`, and serialize deterministically with canonical camel-case field names.
- Each declaration contains one exact, validated operation reference; no route or implementation inference is present.
- Reused `servicefabric_contracts.effects.EffectContract` directly for declared effects.
- Added the local v1 JSON Schema and focused model tests.

## Validation

- `git diff --check` passed.
- `python3 -m compileall packages/servicefabric_capability_model tests/capability_model` passed.
- Focused tests: `PYTHONPATH=packages/servicefabric_capability_model/src:packages/servicefabric_contracts/src /home/lorenzoccasoni/servicefabric-agent-state/wave-04/capability-model/.venv/bin/python -m unittest discover -s tests/capability_model -v` (4 tests passed).

## Boundaries and follow-up

The package does not implement registry storage, invocation, availability, MCP, REST, Python, or `ToolDefinition` projection. The operation-model lane must provide the operation definitions consumed by the opaque exact references before cross-lane integration.

## Candidate commit

Pending candidate commit on `agent/w4-capability-model`.
