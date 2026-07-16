# Wave-6 Task Handoff

Lane: `sdk-agent-projection`
Branch: `agent/w6-sdk-agent-projection`
Base commit: `9b40277fc648e1673a98d32f49ed2d444d632dd3`
Candidate commit: `6963e589766992fe96669f07f03cbcd644a83ce3`

## Changed Paths

- `packages/servicefabric_capability_consumers/**`: dependency-light package containing the generic SDK facade, immutable internal-agent reference, and internal-agent adapter.
- `tests/capability_consumers/**`: focused delegation and immutability coverage.
- `docs/handoffs/wave-06/sdk-agent-projection.md`: canonical specialist handoff.

## Tests Executed

- `python3 -m unittest discover -s tests/capability_consumers -v` — passed, 3 tests.
- `git diff --check` — passed.
- Machine-readable evidence: `.agent-runs/wave-06/sdk-agent-projection/tests.json` (ignored runtime evidence required by the rendered prompt).

## Contracts Consumed

- The Wave-5 `CapabilityRuntimeService.availability(capability_id)` public API.
- The Wave-5 `CapabilityRuntimeService.availability_for_application(application_id)` public API.
- The Wave-5 `CapabilityRuntimeService.invoke(capability_id, input_value)` public API.

## Decisions and Limitations

- `CapabilityClient` delegates availability, application-scoped discovery, and invocation directly to the injected runtime service and returns runtime values unchanged.
- `InternalAgentCapabilityReference` is a frozen, slotted value object containing only the registered capability identifier.
- `InternalAgentCapabilityAdapter` delegates reference availability and invocation directly to the injected runtime service. It performs no endpoint calls, payload rewriting, registry access, or capability business logic.
- The package uses a structural internal protocol so integration can export the facade from the Python client without introducing an import cycle. Runtime construction and Python-client export remain integration-owned.
- Compatibility aliases `AgentCapabilityReference` and `AgentCapabilityAdapter` expose concise internal-agent names without creating additional behavior.

## Blockers

None.

## Rollback

Revert candidate `6963e589766992fe96669f07f03cbcd644a83ce3` and the subsequent handoff commit. No state migration or frozen-contract rollback is required. Do not merge this specialist branch directly.
