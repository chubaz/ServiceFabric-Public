# Tool Lifecycle Contracts v1alpha1

Canonical invocation, result, evidence, effect receipt, and durable-operation envelopes are documented in [Invocation and Result Contracts](invocation-result-v1alpha1.md).

## Resource Boundaries

`ServicePackageDefinition` describes a hosted or referenced package. A package may
implement zero, one, or many operations. `ToolDefinition` describes one stable,
bounded machine-callable operation and never infers package hosting from its ID.

`ToolDefinition` owns semantic intent, behavior, effects, permissions, quality, and
optional projection policy. `ToolRevision` owns one immutable executable contract:
an exact definition reference, package/entrypoint reference, execution binding,
schema references, policy declarations, provenance, and content digest.

`ToolDeployment` is desired placement and routing state for immutable revisions.
`ToolStatus` is mutable observed availability, readiness, maintenance state, and
timestamped conditions. Neither deployment nor status can redefine revision input,
output, effects, or execution behavior.

## Execution Bindings

Bindings are discriminated references for native functions, native services,
immutable graphs, external HTTP operations, declared database operations, bounded
commands, explicitly selected federated MCP tools, and human tasks. They contain no
imports, SQL, shell programs, clients, SDK objects, or credentials. C1-01 validates
reference syntax only; C4 will provide hosting adapters.

## Effects, Authority, and Reliability

Prospective effects declare category, target, scope, reversibility, verification,
approval, and idempotency requirements. `none` cannot coexist with an effectful
category. Permissions and approvals are opaque policy references, never Django
roles, tokens, or database objects.

Every revision declares idempotency class, key support, retry safety, duplicate
delivery behavior, timeout, and cancellation. Effectful revisions cannot leave
idempotency unknown, and irreversible effects cannot claim unrestricted safe retry.
No idempotency store, approval record, or effect receipt is implemented here.

## Revision Immutability and Digest

Revision specifications and their nested execution-significant declarations are
frozen. Collections use immutable tuples. Input and output contracts are immutable
schema references with SHA-256 digests. `content_digest` is represented as SHA-256;
`calculated_content_digest()` deterministically hashes the canonical JSON form of
every revision-spec field except `content_digest`. Publication-time verification and
signing are deferred.

## MCP Projection

MCP projection defaults to disabled. It may provide name, description, annotation,
structured-result, progress, and durable-operation projection policy, but it has no
endpoint, credential, or execution logic. A federated binding names one selected
remote tool. An MCP server package never causes automatic trust or publication of
its full remote inventory.

## Reference Fixtures

- `math.calculate` is deterministic, effect-free, short, and naturally idempotent.
- `research.search_papers` performs cancellable external reads with provider and
  evidence dependencies.
- `project.create_task` requires authority, approval, keyed idempotency, and effect
  verification.

## v1alpha1 Limits

C1-01 defines no invocation/result envelope, runtime error, evidence record, effect
receipt, approval record, idempotency store, registry lookup, router, controller,
hosting adapter, graph runtime, sandbox, MCP handler, or application integration.
Those remain deferred to C1-02 through C1-04 and C2 through C5.
