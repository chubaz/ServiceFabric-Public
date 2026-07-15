# Wave-5 Frozen Contracts

The following boundaries remain unchanged during Wave-5 specialist work:

- the static `CapabilityRegistry` and its persisted definitions;
- `EffectContract` in `servicefabric_contracts.effects`;
- `ToolDefinition` and the AP-01A canonical tool-call behavior;
- accepted Wave-4 `CapabilityDefinition` and `OperationDefinition` shapes;
- the AP-00C managed process runtime.

Runtime availability is a separate derived view sourced from owning-module health. Canonical capability invocation resolves `CapabilityDefinition` → `OperationDefinition` → reviewed HTTP binding → live module endpoint and validates both input and output schemas.

Any frozen-contract change requires a written decision, integration approval, a new bootstrap base, and synchronization of every affected lane.
