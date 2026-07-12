# Invocation and Result Contracts v1alpha1

Protocol adapters authenticate callers and translate HTTP, CLI, graph, scheduled, MCP, or internal requests into `ToolInvocationRequest`. Serialization is not proof of identity: only trusted adapters may populate `CallerContext`. The future invocation pipeline resolves either a deployment target or an explicit immutable revision and creates a narrower `ToolExecutionContext`.

Request IDs identify received envelopes, invocation IDs identify execution attempts, operation IDs identify durable work, correlation IDs group related activity, and idempotency digests represent deduplication intent without exposing raw keys. Budgets are optional bounded authorities; omitted limits remain subject to platform policy and are not unlimited. Child execution may only attenuate inherited budgets, with enforcement deferred to C3.

Synchronous work returns `ToolResult`; durable work is acknowledged with `ToolInvocationAcceptance` and observed through `ServiceFabricOperation`. Success, partial, and error results have distinct invariants. Errors use stable `SF-*` namespaces and caller-safe messages. Evidence is referenced, explicitly classified, and never grants authority.

Declared effects remain part of immutable C1-01 revisions. `ObservedEffect` records what execution observed, while `EffectReceipt` records verification and an idempotency digest. Cancellation is cooperative and does not roll back committed effects.

These contracts contain no HTTP status semantics, MCP result types, credentials, runtime handlers, persistence, routing, approval records, reconciliation logic, or controllers. C1-03 covers legacy translation, C1-04 authoring drafts, C2 registry resolution, C3 runtime enforcement, C4 hosting adapters, and C5 protocol/MCP projection.
