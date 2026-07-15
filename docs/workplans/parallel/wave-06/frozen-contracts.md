# Wave-6 Frozen Contracts

Wave-6 leaves unchanged the Wave-5 `CapabilityRuntimeService`, `CapabilityRegistry`, `CapabilityDefinition`, invocation contracts, operation model, process runtime, canonical contracts, `ToolDefinition`, and AP-01A behavior.

Each projection is a consumer of the Wave-5 public APIs. It may expose only explicitly registered application capabilities and must not contain application-endpoint transport or duplicate canonical invocation.
