# Wave-6 Integration Order

1. Freeze Wave-6 boundaries and launch the MCP, REST, and SDK/agent projection lanes from this bootstrap commit.
2. Review each projection candidate independently for path ownership and delegation through `CapabilityRuntimeService`.
3. Compose the existing MCP gateway and CLI, REST launcher, and Python-client export in integration.
4. Launch and review the one acceptance journey only after all three projections and composition are available.
5. Run `make verify-wave-06`, then run `make verify-current` once at closure.

Candidates are never merged automatically.
