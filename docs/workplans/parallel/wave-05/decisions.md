# Wave-5 Decisions

## Bootstrap decisions

- Static capability registration remains unchanged and independent of runtime availability.
- Availability is deterministic and derives from owning-module health through a bounded source protocol.
- Invocation consumes explicit capability, operation, schema, and binding declarations; it never infers or publishes arbitrary routes.
- HTTP transport accepts reviewed relative paths and methods, invokes loopback endpoints only, handles JSON only, and uses bounded timeouts and safe structured errors.
- Input validation occurs before transport and output validation occurs before a successful canonical result.
- Definitions remain registered when an application module stops; availability then resolves to unavailable with a reason.
- MCP, REST gateway, Python SDK, agent projection, and unrestricted command execution are excluded.
