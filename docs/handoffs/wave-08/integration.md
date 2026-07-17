# Wave-8 integration handoff

## Bootstrap scope

- Added `servicefabric_agent_provider_contracts`; it contains immutable data models
  and `ExecutableHarnessAdapter` only.
- Added a static integration registry and local JSON `ProviderPolicy` loader.
- Reserved the public provider CLI surface without launching a provider.

## Deferred composition

The provider runtime, LangGraph orchestration, and four provider adapters are
specialist-owned and are intentionally not represented by placeholder runtime
implementations. `make verify-wave-08` detects their suites when integrated.

## Validation

Run `make verify-wave-08`. It does not make model-provider calls.
