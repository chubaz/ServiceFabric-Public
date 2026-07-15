# Wave-5 Objective

Base: `53f53ca8a4a9a47887902b84a91bc27a812e9483`.

Add runtime capability availability and canonical capability invocation while preserving static registration and the existing tool runtime.

The acceptance journey is:

```text
servicefabric capabilities register research-notes
servicefabric apps dev start research-notes
servicefabric capabilities availability --application research-notes
servicefabric capabilities invoke notes.create --input JSON
servicefabric capabilities invoke notes.search --input JSON
servicefabric apps dev stop research-notes
servicefabric capabilities availability notes.create
```

After stop, capability definitions remain registered and their runtime availability is `unavailable`.

Wave 5 does not change the static `CapabilityRegistry`, `ToolDefinition`, AP-01A call behavior, or `EffectContract`. It adds no MCP, REST gateway, Python SDK, or agent projection; publishes no routes automatically; and introduces no unrestricted command execution.
