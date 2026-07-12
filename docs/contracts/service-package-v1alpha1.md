# Service Package Contract v1alpha1

## Purpose

`ServicePackageDefinition` is a framework-neutral desired-state declaration for a
hosted, deployable, referenced, or externally operated package. It is not a
`ToolDefinition`: a package can implement zero, one, or many bounded operations.
No operation schema, invocation envelope, deployment status, or registry record is
defined in C1-00.

## Independent Axes

- Hosting declares who operates the implementation: managed container, process,
  static assets, graph, external service, external MCP, or none.
- Artifact identifies that implementation. Managed artifacts require an immutable
  digest or graph revision; external artifacts contain only a reference and endpoint.
- Entrypoint identifies an HTTP API, CLI, web UI, worker, graph, MCP server, or
  library boundary.
- Exposure declares how an entrypoint is reachable: internal, web, CLI, scheduled,
  MCP, or none.

These axes are intentionally separate. A Svelte UI can be `managed_static` plus
`web`, a human-operated calculator can be `managed_process` plus `cli`, and a
worker can have `none` exposure. Neither case creates a tool.

## MCP and External Services

MCP is optional. An MCP exposure names opaque bounded operation references but does
not define their contracts or execute them. An `mcp_server` entrypoint does not
automatically create an MCP exposure. An `external_mcp` package records federation;
it does not make the ServiceFabric gateway the implementation owner.

External HTTP and MCP packages carry an external binding only. They never contain
provider credentials, bearer tokens, registry credentials, or secret values.
Secrets are declared only through `secret://` opaque references and a purpose.

## Declarative Runtime Requirements

Compute, config references, secret references, network policy, storage, and health
are declarations. Network defaults to `none`; egress requires an explicit allowlist.
Health is a desired probe declaration, not live operational state. Live deployment,
health, routing, and evaluation observations remain deferred.

## v1alpha1 Limits

C1-00 does not translate legacy `fabric-manifest.json` files, integrate Django,
Flask, FastAPI, Compose, or MCP, or add a runtime dependency to any production image.
It also does not define tools, revisions, deployment resources, a registry, an
invocation pipeline, graph contracts, hosting adapters, approvals, effect receipts,
or status resources.

Those concerns are deferred to C1-01 through C1-04, C2 Registry, C3 Invocation
Runtime, C4 Hosting Adapters, and C5 MCP Gateway.

The operation-level desired, revision, deployment, and observed-state resources are
documented in `docs/contracts/tool-lifecycle-v1alpha1.md`.
