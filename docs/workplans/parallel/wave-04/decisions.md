# Wave-4 Decisions

## Bootstrap decisions

- Capability registration is explicit and static.
- The application model is layered as Application → Module → Interface → Operation → Capability.
- Capability definitions reuse `EffectContract` and remain independent of MCP, CLI, REST, and Python consumers.
- Research Notes declares three operations and three capabilities; no route-wide inference is permitted.
- Wave-4 does not alter `ToolDefinition`, invoke capabilities, or implement runtime availability.
