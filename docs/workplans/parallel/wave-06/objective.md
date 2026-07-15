# Wave-6 Objective

Base: `9b40277fc648e1673a98d32f49ed2d444d632dd3`.

Expose the existing Wave-5 `CapabilityRuntimeService` through an MCP projection, a local loopback REST gateway, a generic Python client, and an internal agent-consumer adapter. Every projection delegates to the same registered capability, availability, and invocation services.

Wave-6 does not duplicate invocation, call application endpoints from a projection, alter `CapabilityDefinition` or `CapabilityRegistry`, add authentication, remote networking, public hosting, or automatic route publication. REST binds only to `127.0.0.1`.
