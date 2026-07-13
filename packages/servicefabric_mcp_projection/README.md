# ServiceFabric MCP Projection

This package contains only bounded inbound MCP projection models and adapters. It
does not implement canonical tools, governance, durable storage, or outbound MCP
federation.

## Local transports

V4-00 implements an in-process transport for deterministic tests and harnesses.
It has explicit message and response limits and no network binding.

Stdio is deferred because the repository has no approved process lifecycle or
framing host for it. Loopback Streamable HTTP is deferred because the in-process
transport satisfies the local test use case without adding socket lifecycle,
authentication, or public-hosting semantics. Neither deferral changes canonical
invocation or durable-operation behavior.
