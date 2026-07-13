# V4-00 — MCP Projection and Harness Ecosystem

## Status

Current.

## Objective

Implement a bounded ServiceFabric MCP projection gateway and deterministic protocol-harness ecosystem over the canonical tool, runtime, governance, approval, and durable-operation capabilities completed through V3-00.

MCP remains an external protocol projection.

It does not own:

* tool definitions;
* immutable tool revisions;
* tool implementations;
* canonical invocation semantics;
* policy evaluation;
* approval decisions;
* durable-operation state;
* execution retries;
* effect verification;
* reconciliation;
* provider selection.

The completed vertical slice is:

```text
trusted MCP transport or harness input
        ↓
trusted caller and session context construction
        ↓
caller-specific canonical tool discovery
        ↓
MCP tools/list projection
        ↓
MCP tools/call request
        ↓
canonical ToolInvocationRequest translation
        ↓
V3 policy and approval enforcement
        ↓
canonical runtime or durable-operation acceptance
        ↓
canonical result, error, progress, cancellation, or operation state
        ↓
bounded MCP response or compatible task projection
```

## Starting conditions

The following milestones are completed:

```text
E0-00  agent-efficient execution foundation
V1-00  core tool platform
V1-01  agent and external-tool integrations
V2-00  immutable application builder
V2-01  capsule hosting and authoring
V3-00  governance and durable operations
```

V4-00 must preserve all completed milestone contracts and regression gates.

## Governing documents

Implementation must follow:

```text
AGENTS.md
docs/architecture/adr/0001-mcp-is-an-optional-projection.md
docs/architecture/adr/0002-service-package-versus-tool-operation.md
docs/architecture/post-c1-execution-roadmap.md
docs/canonical/ServiceFabric Production Architecture  Roadmap.md
docs/contracts/tool-lifecycle-v1alpha1.md
docs/contracts/invocation-result-v1alpha1.md
docs/workplans/milestones/v3-00-governance-and-durable-operations.md
```

Use the MCP profile pinned by the repository architecture. Do not silently upgrade the protocol profile during this milestone.

## Architectural invariants

### Canonical ownership

ServiceFabric-native contracts remain authoritative.

MCP-specific objects may project canonical resources, but they must not redefine:

```text
ToolDefinition
ToolRevision
ToolInvocationRequest
ToolInvocationAcceptance
ToolResult
ToolError
ServiceFabricOperation
PolicyDecision
ApprovalBinding
ObservedEffect
EffectReceipt
ReconciliationRecord
```

### Separation of concerns

Keep these concerns separate:

```text
tool implementation
tool hosting
canonical execution
governance
durable operation management
MCP exposure
outbound MCP federation
```

A package may exist without MCP exposure.

An MCP-enabled tool is not necessarily available to every caller.

An outbound federated MCP server is not automatically exposed through the inbound ServiceFabric gateway.

### Gateway limitations

The gateway must not:

* implement domain tools;
* import tool implementation modules;
* choose providers;
* contain business policy;
* create approval authority;
* store credentials;
* retry external effects;
* maintain a competing durable-operation store;
* publish arbitrary remote MCP inventories;
* execute shell commands;
* spawn unrestricted subprocesses.

## Scope

V4-00 includes:

* MCP projection models and validation;
* trusted transport/session context;
* caller-specific tool discovery;
* deterministic tool metadata projection;
* MCP call translation into canonical requests;
* canonical result and error projection;
* progress projection;
* cancellation delegation;
* compatible durable-operation/task projection;
* bounded session and capability negotiation;
* deterministic in-process transport;
* bounded local-development transports justified by the implementation;
* protocol harnesses;
* golden transcripts;
* replay fixtures;
* malformed-message and resource-limit testing;
* typed Python client and machine-readable CLI support;
* architecture guardrails;
* CI package installation and V4 verification.

## Explicit exclusions

V4-00 must not introduce:

```text
production identity provider
public multi-tenant MCP service
public internet binding
production TLS or domains
production ingress
Kubernetes
PostgreSQL
Redis
NATS
distributed session storage
distributed MCP gateway replicas
production rate-limit infrastructure
arbitrary remote MCP discovery
remote inventory auto-publication
provider selection inside the gateway
business policy inside the gateway
tool implementations inside MCP packages
external-effect retries inside the gateway
a second authoritative operation store
general-purpose shell execution
arbitrary subprocess execution
real irreversible effects
database migrations
Compose changes
Nginx changes
V5 production-control-plane work
```

## Package and service boundaries

Inventory existing repository conventions before finalizing package names.

The preferred structure is:

```text
packages/servicefabric_mcp_projection
packages/servicefabric_mcp_harness
services/mcp_gateway
```

The existing package:

```text
packages/servicefabric_mcp_client
```

remains the outbound allowlisted federated MCP client adapter.

It must not become the inbound ServiceFabric MCP gateway.

Suggested dependency direction:

```text
servicefabric_contracts
        ↑
servicefabric_runtime
servicefabric_governance
servicefabric_operations
        ↑
servicefabric_mcp_projection
        ↑
mcp_gateway service
        ↑
client and harness adapters
```

Canonical packages must not import MCP projection, gateway, transport, or harness packages.

MCP protocol DTOs belong in projection packages, not in `servicefabric_contracts`.

## Projection contracts

The `projection-contracts` phase must define bounded MCP-specific types for the repository-selected MCP profile.

Expected concepts include:

```text
MCP client capabilities
MCP server capabilities
MCP session context
projected MCP tool
projected tool page
projected call request
projected call response
projected progress notification
projected cancellation request
projected task or durable-operation view
projected protocol error
bounded protocol envelope
```

Names should follow the selected MCP profile and existing repository conventions.

Projection objects must:

* reject undeclared fields where locally modeled;
* use bounded strings and collections;
* have deterministic serialization;
* avoid filesystem paths;
* avoid credentials;
* avoid raw idempotency keys;
* avoid executable entrypoints;
* avoid internal policy details;
* avoid approval tokens;
* avoid raw exception objects.

Do not add protocol-specific fields to canonical contracts merely for convenience.

## Trusted caller and session context

The transport adapter is responsible for constructing trusted context.

Caller-supplied JSON must never establish:

* authenticated identity;
* authority;
* roles;
* approval rights;
* tenant membership;
* trusted session metadata.

The initial local implementation may use explicit trusted fixtures or adapter-injected principals.

It must not claim to provide production authentication.

Session context must be:

* bounded;
* non-authoritative;
* isolated between clients;
* safe to discard;
* reconstructable where practical.

Loss of an MCP session must not destroy an accepted durable ServiceFabric operation.

## Caller-specific discovery

Implement deterministic caller-specific tool discovery.

A tool is eligible for MCP projection only when all required conditions hold:

* the canonical definition exists;
* an immutable revision resolves successfully;
* MCP projection is explicitly enabled;
* the revision is not disabled, unavailable, or ineligible;
* the caller is permitted to discover it;
* projection constraints are satisfied.

Discovery must not automatically expose:

* all packages;
* all tools;
* every revision;
* disabled projections;
* deprecated or unavailable revisions;
* every tool from a federated MCP server;
* tools unavailable to the caller.

Discovery output must have:

* deterministic ordering;
* stable projected names;
* bounded result counts;
* deterministic pagination or cursor semantics if pagination is implemented;
* no credential or internal-path leakage.

## Tool metadata projection

Project canonical tool semantics without changing them.

Projected metadata may include:

* stable tool name;
* safe description;
* input schema;
* structured-output support;
* safe annotations;
* progress support;
* cancellation support;
* durable-operation capability.

The gateway must not infer effects, risk, permissions, or idempotency behavior from MCP metadata.

Those remain canonical ServiceFabric declarations.

Projected schemas must remain tied to the resolved immutable revision.

## Call translation

Translate MCP tool calls into canonical `ToolInvocationRequest` resources.

Translation must preserve or establish:

```text
trusted request identity
correlation identity
resolved immutable revision
validated arguments
trusted caller context
idempotency intent
deadline or timeout
cancellation context
projection metadata
```

The gateway must invoke canonical runtime or service boundaries.

It must not call domain implementations directly.

It must not bypass:

* policy evaluation;
* approval requirements;
* exact-intent approval binding;
* idempotency handling;
* durable-operation acceptance;
* effect verification.

Malformed calls must fail before canonical execution.

## Governance integration

MCP projection must delegate governance decisions to V3 services.

Required behaviors include:

```text
allowed call
denied call
approval-required call
approved call
constrained allow
expired or invalid approval
changed-intent approval rejection
```

Protocol responses may safely explain that authorization or approval is required, but must not disclose sensitive policy internals.

MCP session state is not approval authority.

## Result projection

Project canonical results deterministically.

Support:

* structured result projection when compatible;
* safe textual fallback;
* bounded response content;
* evidence references where permitted;
* durable acceptance responses;
* terminal durable results.

The projection layer must not mutate canonical results.

Large outputs must follow explicit limits rather than being silently emitted without bounds.

## Error projection

Define stable mappings from canonical error classes to MCP-compatible errors.

Cover at least:

```text
validation
not found
revision conflict
authorization denied
approval required
approval invalid
idempotency conflict
timeout
cancellation
dependency unavailable
execution failure
effect uncertainty
internal projection failure
```

Error projection must not expose:

* Python tracebacks;
* raw exception representations;
* filesystem paths;
* provider credentials;
* secret values;
* internal policy documents;
* storage implementation details.

Unknown internal failures must become a bounded safe internal error.

## Progress projection

Progress must come from canonical invocation or operation evidence.

The gateway must not fabricate progress from transport activity.

Progress projection must:

* bind to the correct request or operation;
* preserve ordering where available;
* remain bounded;
* tolerate clients without progress support;
* avoid leaking internal event payloads.

## Cancellation

MCP cancellation requests must delegate to canonical cancellation boundaries.

The gateway must not:

* kill arbitrary processes;
* edit durable records directly;
* mutate immutable history;
* claim to reverse committed effects.

Cancellation behavior must preserve V3 cooperative-cancellation semantics.

## Durable-operation projection

`ServiceFabricOperation` remains authoritative.

Where the selected MCP profile supports compatible task semantics, implement an optional projection from canonical durable operations.

Project only safe fields, including:

```text
operation identity
projected state
progress
safe timestamps
cancellation state
terminal result
terminal error
bounded evidence references
```

Do not maintain an independent authoritative MCP task store.

Protocol task identity must resolve back to a canonical ServiceFabric operation.

Clients without task support must receive a compatible bounded response without changing the canonical operation lifecycle.

## Session and capability negotiation

Implement bounded initialization and capability negotiation.

Cover:

* protocol/profile compatibility;
* client capabilities;
* server capabilities;
* supported projection features;
* progress support;
* cancellation support;
* structured-output support;
* durable-operation projection support;
* transport capabilities.

Reject unsupported or contradictory initialization sequences.

Session state must have explicit limits for:

* maximum sessions;
* maximum requests;
* maximum message size;
* idle time where relevant;
* lifetime where relevant.

## Local transports

V4-00 must include a deterministic in-process transport for tests and harnesses.

Evaluate:

```text
stdio
loopback-only Streamable HTTP
```

Implement only transports justified by the final workplan and repository dependencies.

A local HTTP transport, when implemented, must:

* bind only to loopback;
* use bounded request sizes;
* use bounded response sizes;
* reject unsupported methods;
* apply session and request limits;
* avoid public authentication claims;
* avoid production TLS claims;
* shut down cleanly.

A stdio implementation must:

* use bounded input;
* use bounded output;
* avoid executing shell commands;
* avoid spawning arbitrary subprocesses;
* separate protocol framing from business logic.

## Harness ecosystem

Implement deterministic MCP projection harnesses.

The harness must support:

* in-process client/server exchange;
* fixed trusted caller contexts;
* fixed clocks;
* fixed identifiers;
* deterministic tool inventories;
* golden protocol transcripts;
* request and response replay;
* capability-negotiation fixtures;
* discovery fixtures;
* call fixtures;
* structured-result fixtures;
* safe error fixtures;
* progress fixtures;
* cancellation fixtures;
* durable-operation fixtures;
* malformed-message fixtures;
* size-limit fixtures;
* session-isolation fixtures.

Harnesses must not require:

```text
external network access
Docker
paid providers
production credentials
real irreversible effects
```

Golden transcripts must be deterministic across repeated runs.

## Federated MCP separation

Outbound federation and inbound projection are separate concerns.

The existing federated MCP client may execute an explicitly selected, schema-pinned remote tool through a canonical ServiceFabric binding.

The inbound gateway must not:

* mirror arbitrary remote inventories;
* treat a remote server as trusted merely because it speaks MCP;
* inherit remote descriptions as canonical authority;
* bypass canonical tool review;
* bypass policy;
* publish unselected remote tools.

## Service boundary

The gateway service coordinates:

* trusted context construction;
* session negotiation;
* caller-specific discovery;
* tool projection;
* call translation;
* canonical service delegation;
* result and error projection;
* progress;
* cancellation;
* durable-operation projection.

It contains no domain tool implementation.

Transport adapters must delegate to the same gateway service rather than duplicate projection logic.

## Python client and CLI

Extend the Python client through typed service delegation.

Potential operations include:

```text
initialize MCP session
list projected tools
describe projected tool
call projected tool
inspect durable projected task
request cancellation
replay harness transcript
validate transcript
```

The client must not:

* manipulate gateway session internals;
* access durable stores directly;
* bypass canonical runtime;
* create trusted caller authority from user-provided fields.

CLI output must be deterministic, bounded, and machine-readable.

## Security and limits

Require explicit limits for:

```text
request bytes
response bytes
tool count
page size
tool-name length
description length
argument depth
argument size
session count
requests per session
progress event count
transcript size
evidence-reference count
```

Security tests must prove:

* caller-supplied identity is untrusted;
* disabled projections are hidden;
* policy denial cannot be bypassed;
* approval requirements cannot be bypassed;
* raw secrets are never projected;
* raw idempotency keys are never projected;
* internal paths are never projected;
* remote inventories are not auto-published;
* cancellation delegates through canonical services;
* task projection is non-authoritative;
* no shell execution is introduced;
* no public binding is introduced.

## Testing strategy

Add focused tests for:

```text
projection model validation
deterministic serialization
initialization
capability negotiation
caller-specific tools/list
deterministic discovery ordering
bounded pagination or cursors
disabled projection
unavailable revisions
malformed projection metadata
tools/call translation
immutable revision binding
argument validation
idempotency translation
policy allow
policy denial
approval required
approval granted
approval mismatch
synchronous canonical result
structured result
safe text fallback
error normalization
progress ordering
progress limits
cancellation delegation
durable acceptance
operation status projection
terminal durable result
durable cancellation
lost-session operation survival
malformed messages
request-size limits
response-size limits
session limits
session isolation
golden transcript determinism
transcript replay
stdio behavior where implemented
loopback behavior where implemented
service delegation
client delegation
CLI JSON output
outbound federation separation
V3 regressions
architecture boundaries
```

## Verification configuration

V4 readiness must include:

```text
v3-00 completion
workplan validation
architecture guardrails
dependency-lock validation
```

V4 completion must include named checks for:

```text
v4-00-projection-contracts
v4-00-discovery
v4-00-call-translation
v4-00-results-errors
v4-00-progress-cancellation
v4-00-durable-projection
v4-00-sessions
v4-00-transports
v4-00-harness
v4-00-client-integration
v4-00-boundaries
schema-snapshots
dependency-locks
architecture-guardrails
v3-00-regressions
compileall
pip-check
diff-check
```

Completion checks remain `planned: true` until their implementation exists.

Every planned check must contain a valid command array.

At V4 completion, no completion check may remain planned.

## Implementation phases

Execute sequentially.

Run focused tests, update status, and commit every phase before beginning the next.

1. `projection-contracts`

   * define bounded MCP-specific projection and envelope types;
   * define deterministic serialization;
   * add validation and protocol fixtures;
   * add projection-boundary tests.

2. `discovery-projection`

   * implement caller-specific canonical discovery;
   * enforce MCP-enabled projection;
   * implement deterministic ordering and limits;
   * reject automatic remote inventory exposure.

3. `call-translation`

   * translate MCP calls into canonical invocation requests;
   * preserve revision, arguments, caller, correlation, deadlines, and idempotency;
   * delegate through canonical runtime and governance boundaries.

4. `result-and-error-projection`

   * project structured results and safe text fallbacks;
   * add stable canonical-to-MCP error mappings;
   * enforce output limits and redaction.

5. `progress-and-cancellation`

   * project canonical progress evidence;
   * delegate cancellation;
   * preserve cooperative-cancellation semantics.

6. `durable-operation-projection`

   * project ServiceFabric operations into compatible task views;
   * keep canonical operations authoritative;
   * support task-capable and task-incapable clients.

7. `session-and-capability-negotiation`

   * implement initialization;
   * negotiate capabilities;
   * enforce bounded non-authoritative sessions.

8. `local-transports`

   * implement deterministic in-process transport;
   * add justified stdio or loopback transport;
   * enforce message and lifecycle limits.

9. `harness-and-transcript-ecosystem`

   * implement deterministic harnesses;
   * add fixed fixtures, golden transcripts, and replay;
   * add malformed-message and limit tests.

10. `client-cli-and-integration`

    * add typed Python client delegation;
    * add machine-readable CLI behavior;
    * verify complete canonical V1–V4 vertical slices.

11. `cross-boundary-verification`

    * complete architecture checks;
    * complete transport cleanup checks;
    * run V3 regressions;
    * verify locks, schemas, imports, compilation, CI, and diff hygiene.

## Suggested commit sequence

```text
feat: add MCP projection contracts
feat: add caller-specific MCP discovery
feat: translate MCP calls to canonical invocations
feat: project canonical MCP results and errors
feat: add MCP progress and cancellation projection
feat: project durable operations as MCP tasks
feat: add MCP session capability negotiation
feat: add bounded local MCP transports
feat: add deterministic MCP harnesses and transcripts
feat: add MCP gateway client and CLI integration
test: verify V4-00 projection boundaries
docs: complete V4-00 milestone status
```

## CI requirements

Refactoring CI must:

* install every V4 package explicitly;
* use the active Python interpreter;
* use no machine-local virtual-environment paths;
* use no `PYTHONPATH` workaround;
* run an import smoke test;
* run V4 completion verification;
* retain V3 regression verification.

Potential package installations include:

```text
packages/servicefabric_mcp_projection
packages/servicefabric_mcp_harness
services/mcp_gateway
clients/python
```

Use the final package paths actually created by the implementation.

## Acceptance criteria

V4-00 is complete only when:

* MCP remains an optional external projection;
* canonical contracts remain authoritative;
* discovery is caller-specific and deterministic;
* disabled or unauthorized tools remain hidden;
* arbitrary federated inventories are never auto-published;
* projected metadata is safe and bounded;
* calls translate into canonical invocation requests;
* V3 policy and approval cannot be bypassed;
* structured results project deterministically;
* canonical errors map to safe protocol errors;
* progress originates from canonical evidence;
* cancellation delegates through canonical services;
* durable operations remain authoritative;
* session loss does not destroy accepted operations;
* local transports are bounded and non-public;
* golden transcripts are deterministic;
* transcript replay is stable;
* client and CLI delegate through gateway boundaries;
* every V4 verification check passes;
* V3 remains passing;
* no production topology or V5 work is introduced.

## Stop conditions

Stop and report when implementation would require:

* production identity infrastructure;
* public multi-tenant hosting;
* production TLS or ingress;
* distributed gateway coordination;
* database-backed sessions;
* arbitrary remote inventory publication;
* business policy inside the gateway;
* direct domain-tool execution inside MCP packages;
* external-effect retry ownership in the gateway;
* a competing durable-operation store;
* weakening canonical V3 invariants;
* arbitrary code or shell execution;
* database migrations;
* Compose or Nginx changes;
* V5 implementation.

Ordinary implementation difficulty or failing tests are not stop conditions.

## Known limitations

The initial V4 implementation remains:

```text
local development and test focused
single-process
non-production identity
non-production session handling
non-public
non-distributed
without production TLS
without public ingress
without Kubernetes
without PostgreSQL
without Redis
without NATS
without production rate limiting
without remote inventory auto-publication
without real irreversible external effects
```

## Rollback

Revert the V4 commits and remove explicitly configured temporary harness, transcript, session, or transport-test directories.

Rollback must not require:

```text
database cleanup
migration rollback
Compose rollback
Nginx rollback
Kubernetes cleanup
DNS cleanup
TLS cleanup
production-effect cleanup
```

## Completion report

The implementation agent must report:

```text
Blockers
Changed areas
Commit sequence and SHAs
Projection architecture
Canonical contracts reused
MCP-specific models introduced
Discovery behavior
Call translation
Governance behavior
Result and error projection
Progress and cancellation
Durable-operation projection
Session and capability negotiation
Transport behavior
Harness and transcript behavior
Client and CLI behavior
Security and architecture guardrails
Verification configuration
Exact test counts
V3 regression result
CI changes
Environment limitations
Deviations
Known limitations
Rollback
Working-tree status
PR-ready summary
Next-session prompt
```

At branch completion, keep V4-00 current with phase `completed` until its pull request is merged.

Do not implement a later milestone in the V4 branch.
