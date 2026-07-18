# ServiceFabric product overview

ServiceFabric is a canonical package and tool platform for assembling, running, and governing application capabilities. Its runtime contract is independent of any one consumer protocol: calls enter as `ToolInvocationRequest` records and complete as `ToolResult` records. A service package may implement zero, one, or many tools; a `ToolDefinition` is not a package.

## Foundation architecture

```text
Package definitions and immutable revisions
                |
Canonical contracts -> runtime -> operation and capability services
                |                         |
     application models/builders     results, evidence, effects
                |
factory, blueprint, and agentic workflows
                |
reviewed distillation proposals -> approved authoritative catalogs
```

The contracts, runtime, operations, and capability packages form the stable centre. Application models and builders compose that centre into applications. Factory and engineering-blueprint packages support repeatable creation. Agentic orchestration and provider adapters remain consumers of the canonical runtime rather than alternate execution substrates.

MCP is an optional projection at the boundary. It neither owns runtime behavior nor replaces canonical invocation and result contracts. Legacy numbered services remain contained compatibility context, not the primary product architecture.

## Release boundary

The foundation release is a source-level, locally verifiable engineering release. Its [manifest](../../packages/servicefabric_release_readiness/servicefabric_release_readiness/foundation_release.json) declares the package integrity surface, and `servicefabric doctor` checks it without mutation. It is not a hosted control plane, marketplace, or automated publication authority.
