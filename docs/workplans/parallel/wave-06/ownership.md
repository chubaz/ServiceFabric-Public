# Wave-6 Ownership

| Lane | Owned scope |
| --- | --- |
| integration | MCP gateway and CLI wiring, REST composition and launch command, Python-client export, dependency/CI wiring, candidate review, and closure |
| mcp-projection | `packages/servicefabric_capability_mcp_projection/**`, `tests/capability_mcp_projection/**`, and handoff; maximum three focused tests |
| rest-projection | `services/capability_rest_gateway/**`, `tests/capability_rest_gateway/**`, and handoff; maximum three focused tests |
| sdk-agent-projection | `packages/servicefabric_capability_consumers/**`, `tests/capability_consumers/**`, and handoff; maximum three focused tests |
| acceptance | `tests/wave_06/**` and handoff; one end-to-end journey after composition |

Specialists create focused candidate commits only. The integration lane reviews and composes candidates but does not implement specialist functionality.
