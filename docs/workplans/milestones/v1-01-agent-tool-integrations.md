# V1-01 — Agent and External-Tool Integrations

## 1. Objective

Make the canonical ServiceFabric tool portfolio usable from agentic frameworks and coding harnesses without making MCP the internal runtime substrate.

Deliver one reviewed demonstration toolset containing:

```text
math.calculate
research.search_papers
research.prepare_literature_review
```

The three tools must demonstrate:

```text
math.calculate
    trusted native primitive

research.search_papers
    explicitly approved federated MCP operation

research.prepare_literature_review
    bounded composite LangGraph operation
```

The same toolset must be accessible through:

```text
Python ServiceFabric client
existing ServiceFabric CLI
LangChain/LangGraph
Pi extension
```

All calls must continue to enter through the canonical ServiceFabric invocation boundary and return canonical ServiceFabric results.

V1-01 must not introduce a ServiceFabric MCP server or gateway.

---

# 2. Starting conditions

Start from the merged V1-00 milestone.

Required baseline:

```text
E0-00 completed
V1-00 completed
V1-01 current
working tree clean
canonical specification hashes valid
ServiceFabric contract tests passing
V1-00 runtime and client tests passing
portfolio and math.calculate vertical slice operational
```

Before editing, run:

```bash
make agent-preflight
make agent-context
make verify-current
```

At the beginning of V1-01, `make verify-current` may run readiness checks because V1-01 completion checks are still marked as planned.

Before merging V1-01, replace every planned completion check with the actual commands required to validate the implemented integrations.

---

# 3. Governing decisions and documents

Read:

```text
AGENTS.md
docs/workplans/current.md

docs/architecture/adr/0001-mcp-is-an-optional-projection.md
docs/architecture/adr/0002-service-package-versus-tool-operation.md
docs/architecture/adr/0005-repository-native-agent-execution.md

docs/contracts/service-package-v1alpha1.md
docs/contracts/tool-lifecycle-v1alpha1.md
docs/contracts/invocation-result-v1alpha1.md

packages/servicefabric_runtime/
clients/python/
```

Read the V1-00 portfolio, runtime, client, CLI, and `math.calculate` implementation before designing new integration packages.

Do not reread all canonical specifications unless the hash check reports drift or a material ambiguity cannot be resolved from the local ADRs and contract guides.

---

# 4. Architectural rules

## 4.1 Canonical runtime ownership

ServiceFabric owns:

```text
tool identity
tool revisions
toolsets
portfolio resolution
input and output validation
trusted caller context
execution selection
timeouts and cancellation
result normalization
effects and evidence boundaries
```

Consumer adapters own only projection into their host framework.

No consumer adapter may execute tool business logic directly.

## 4.2 MCP remains external or projected

For V1-01, MCP is used only as an external provider protocol:

```text
ServiceFabric runtime
    → approved federated MCP client adapter
    → explicitly configured MCP server
    → explicitly selected remote tool
```

Do not create:

```text
ServiceFabric MCP server
MCP gateway
tools/list endpoint owned by ServiceFabric
tools/call endpoint owned by ServiceFabric
generic MCP proxy
automatic import of all remote tools
```

## 4.3 Composite graph rule

A composite LangGraph tool must invoke primitive tools through the ServiceFabric client or canonical runtime boundary.

It must not invoke:

```text
native tool functions directly
MCP clients directly
portfolio internals directly
execution adapters directly
```

## 4.4 Trusted identity rule

LangChain graph state, model-generated arguments, Pi tool arguments, and remote MCP content are not trusted identity sources.

Only a trusted consumer adapter or runtime boundary may construct authoritative caller context.

---

# 5. Scope

V1-01 includes:

```text
approved federated MCP client adapter
research.search_papers canonical resources
LangChain tool projection
LangGraph composite-tool execution
research.prepare_literature_review canonical resources
Pi ServiceFabric extension
research-demo toolset
cross-consumer tests and documentation
```

V1-01 excludes:

```text
ServiceFabric MCP gateway
remote ServiceFabric HTTP transport, unless strictly necessary and separately justified
database registry
durable operation persistence
Django authoring
application builder
general command runner
sandbox
workstation mutation
approval engine
production credential backend
automatic MCP discovery publication
```

---

# 6. Expected implementation areas

Use the existing repository layout established by V1-00.

Expected additions:

```text
packages/
├── servicefabric_mcp_client/
└── servicefabric_langchain/

services/
└── graph_runner/

integrations/
└── pi-servicefabric/

portfolio/
├── packages/
├── tools/
│   ├── definitions/
│   └── revisions/
├── toolsets/
└── external-servers/

tests/
├── integrations/
├── langchain/
├── mcp/
├── graph/
└── pi/
```

Adjust paths only where the V1-00 repository conventions make another location clearly preferable.

Do not reorganize existing V1-00 code merely to match this conceptual tree.

---

# 7. Phase 1 — Federated MCP client adapter

## 7.1 Objective

Allow the canonical runtime to invoke one explicitly approved operation hosted by an existing MCP server.

The adapter is an execution adapter, not a gateway.

## 7.2 Package

Create:

```text
packages/servicefabric_mcp_client/
```

Suggested modules:

```text
configuration.py
transport.py
discovery.py
schema.py
adapter.py
errors.py
testing.py
```

Keep MCP-specific dependencies isolated inside this package.

The canonical contract and runtime-core packages must not import the MCP SDK.

## 7.3 Approved server configuration

Represent an external MCP server through a reviewed configuration file.

Example shape:

```yaml
server_id: research-provider
transport: streamable_http
endpoint_ref: endpoint:research-provider
credential_binding_ref: credential:research-provider

allowed_tools:
  - remote_name: search_papers
    canonical_tool_id: research.search_papers
    expected_schema_digest: sha256:...
```

JSON may be used instead if the portfolio currently uses JSON exclusively.

The configuration must not contain:

```text
bearer tokens
API keys
OAuth access tokens
cookies
raw authorization headers
arbitrary STDIO shell commands
```

## 7.4 Explicit selection

The adapter must invoke only operations listed in `allowed_tools`.

It must never treat the result of remote `tools/list` as an automatic ServiceFabric portfolio update.

Remote tool discovery is used only to:

```text
confirm the selected tool exists
normalize its schema
compare the schema digest
obtain protocol metadata needed for invocation
```

## 7.5 Schema drift

At startup or connection time:

```text
discover selected remote tool
normalize its input schema deterministically
calculate schema digest
compare with reviewed expected digest
```

On incompatible drift:

```text
disable the canonical tool
return a stable dependency or contract error
record a safe diagnostic
do not invoke the changed remote operation
```

Do not silently accept drift because the remote tool name remains unchanged.

## 7.6 Initial transport

Prefer:

```text
Streamable HTTP
```

An STDIO transport may be added only if:

```text
the executable is operator configured
the executable and arguments are allowlisted
no shell string is evaluated
the process is bounded and cancellable
```

Do not permit portfolio-authored arbitrary commands.

## 7.7 Result handling

Map remote MCP results into canonical `ToolResult`.

Requirements:

```text
structured result preserved when available
text content safely represented
remote errors normalized into ToolError
remote stack traces not exposed
remote annotations not trusted as policy
remote effect claims not treated as verified receipts
cancellation propagated where transport permits
timeouts enforced by ServiceFabric
```

---

# 8. Phase 2 — `research.search_papers`

Add canonical resources for:

```text
research.search_papers
```

## 8.1 Tool semantics

Declare it as:

```text
external read operation
conditionally deterministic or nondeterministic
provider dependent
bounded timeout
cancellable where supported
evidence producing
effect class: external_read
```

## 8.2 Revision binding

Use:

```text
execution_binding = federated_mcp
```

Reference:

```text
approved external MCP package/server
selected remote tool name
reviewed schema digest
```

Do not put the provider endpoint or credential in `ToolDefinition`.

## 8.3 Input

Use a bounded research-oriented input such as:

```text
query
maximum_results
year_from
year_to
language
```

Avoid exposing the full remote provider schema merely because it exists.

The canonical tool should present the smallest stable useful contract.

## 8.4 Output

Use a structured output containing bounded paper records such as:

```text
title
authors
year
abstract or summary
provider identifier
source locator
citation metadata where available
```

Do not return raw unbounded provider payloads.

## 8.5 Evidence

Where possible, create `EvidenceRecord` references for returned papers or provider records.

Provider data remains externally sourced and is not automatically classified as verified truth.

---

# 9. Phase 3 — LangChain projection

## 9.1 Package

Create:

```text
packages/servicefabric_langchain/
```

Keep all LangChain and LangGraph dependencies isolated from:

```text
servicefabric_contracts
servicefabric_runtime core
portfolio resolver
MCP client adapter
```

## 9.2 Public API

Provide an API similar to:

```python
toolset = ServiceFabricToolset(
    client=client,
    toolset_id="research-demo",
)

tools = await toolset.load_tools()
```

Also permit loading an individual tool where useful:

```python
tool = await ServiceFabricTool.from_id(
    client=client,
    tool_id="research.search_papers",
)
```

The exact API may follow established repository style.

## 9.3 Projection behavior

For each canonical tool:

```text
resolve immutable revision
load canonical input schema
derive consumer-safe tool name
derive concise consumer description
create LangChain-compatible structured tool
```

Do not mutate canonical schemas silently to accommodate one model provider.

Schema incompatibility must produce an explicit diagnostic.

## 9.4 Invocation behavior

A projected LangChain tool must:

```text
accept model-visible business arguments only
construct a canonical ToolInvocationRequest
pass trusted context separately
invoke through ServiceFabricClient
return normalized output
```

It must not expose to the model:

```text
credentials
caller scopes
approval references
internal endpoints
deployment internals
raw idempotency material
```

## 9.5 Result mapping

Map:

```text
success
    → ordinary structured tool output

partial
    → usable structured output plus warnings

error
    → safe framework-compatible tool error

evidence
    → structured artifact or metadata where supported

effect receipts
    → structured details, never hidden in prose
```

---

# 10. Phase 4 — Composite LangGraph tool

## 10.1 Objective

Implement:

```text
research.prepare_literature_review
```

as one bounded canonical tool backed by a LangGraph graph.

## 10.2 Canonical model

Use:

```text
ServicePackageDefinition
    hosting = managed_graph
    entrypoint = graph

ToolDefinition
    research.prepare_literature_review

ToolRevision
    execution_binding = internal_graph
```

The graph revision must be immutable or content-addressed.

## 10.3 Initial graph behavior

A minimal useful graph may:

```text
validate and normalize the research question
invoke research.search_papers
rank or filter results
prepare a structured literature-review summary
return evidence references and warnings
```

The implementation may use deterministic placeholder synthesis or a fake model in tests.

Do not require paid model calls in CI.

## 10.4 Nested calls

The graph must invoke `research.search_papers` through the canonical client/runtime.

Propagate:

```text
root correlation ID
parent invocation reference
effective budget
cancellation
toolset authority
```

Child calls must not receive greater budget or authority than the parent.

## 10.5 Cycle and depth safety

Add a bounded nesting/depth rule.

The graph must not recursively invoke itself without an explicit lower depth bound.

## 10.6 Error behavior

Normalize graph failures into stable canonical errors.

A provider failure may produce:

```text
partial result
warning
evidence from successful sources
```

where the result remains meaningfully usable.

---

# 11. Phase 5 — Pi ServiceFabric extension

## 11.1 Objective

Expose the reviewed ServiceFabric toolset inside Pi through a native extension.

Do not require an MCP gateway for Pi.

## 11.2 Package

Create:

```text
integrations/pi-servicefabric/
```

Suggested contents:

```text
package.json
tsconfig.json
src/
  index.ts
  client.ts
  discovery.ts
  schema.ts
  results.ts
  commands.ts
tests/
```

Use pinned and reproducible TypeScript dependencies.

Do not run `npm install` during application startup.

## 11.3 Configuration

Configuration may include:

```text
ServiceFabric runtime/client location
selected toolset ID
credential-provider reference
timeouts
display preferences
```

Do not place credentials in committed configuration.

## 11.4 Discovery

At extension startup or explicit refresh:

```text
load selected toolset
resolve consumer-safe tool metadata
verify portfolio snapshot or resource digest
register only selected tools
```

Do not expose the complete portfolio automatically.

## 11.5 Tool registration

Translate canonical input JSON Schema into the schema format expected by Pi’s extension API.

Every registered Pi tool must invoke ServiceFabric rather than executing business logic locally.

## 11.6 Cancellation and progress

Map Pi cancellation signals to the canonical cancellation boundary.

Progress may be shown when the runtime or graph adapter provides it.

Do not invent progress values.

## 11.7 Commands

Provide:

```text
/sf-status
/sf-toolsets
/sf-toolset
/sf-tools
/sf-refresh
```

Commands should show concise, safe information.

## 11.8 Effectful-tool rule

Pi-side confirmation may improve user experience but is not authoritative authorization.

Future effectful tools must still pass ServiceFabric policy and approval controls.

---

# 12. Phase 6 — Research demonstration toolset

Create:

```text
research-demo
```

or the canonical identifier format already established by V1-00.

Members:

```text
math.calculate
research.search_papers
research.prepare_literature_review
```

The toolset must reference explicit immutable revisions.

It should initially permit consumers:

```text
python
cli
langchain
langgraph
pi
```

Consumer declarations may be documentation or metadata if no canonical consumer-policy field exists yet.

Do not invent speculative contract fields merely for this workplan.

## 12.1 Permissions

The demonstration toolset should remain:

```text
effect-free or external-read only
non-privileged
non-workstation-mutating
```

This keeps V1-01 focused on integration rather than approval governance.

---

# 13. Cross-consumer behavior

The same canonical tools must behave consistently across consumers.

## Python client

Validate:

```text
toolset discovery
native invocation
MCP-backed invocation
composite graph invocation
structured success
partial response
safe error
```

## CLI

Validate:

```text
list research-demo
describe each tool
invoke each tool
JSON output mode
safe exit codes
```

## LangGraph

Validate:

```text
load named toolset
invoke all three tools
preserve schemas
propagate correlation
handle partial and error results
```

## Pi

Validate:

```text
register selected tools
invoke all three implementation types
cancel a bounded invocation
refresh tool metadata
render safe structured results
```

No consumer may maintain an independent copy of tool business logic.

---

# 14. Testing strategy

## 14.1 No required external service in CI

CI must not require a public MCP provider.

Implement a deterministic fake MCP server or transport fixture that supports:

```text
tools/list
selected search_papers schema
tools/call
success
partial response
provider failure
schema drift
timeout
cancellation where practical
```

The fake must be clearly test-only.

## 14.2 MCP tests

Cover:

```text
selected tool available
unapproved tool rejected
unknown tool rejected
schema digest match
schema drift rejection
safe remote error mapping
timeout
credential absence
no automatic portfolio mutation
```

## 14.3 LangChain tests

Cover:

```text
schema projection
stable tool name
canonical invocation construction
trusted context kept outside arguments
success mapping
partial mapping
error mapping
```

Use fake or deterministic models only.

## 14.4 Composite graph tests

Cover:

```text
nested canonical call
correlation propagation
budget attenuation
depth bound
provider partial result
cancellation
safe graph error
```

## 14.5 Pi tests

Cover:

```text
tool registration
schema conversion
selected-toolset restriction
request construction
result rendering
cancellation mapping
safe configuration
```

Do not require launching an interactive Pi process in CI where unit-level extension tests suffice.

## 14.6 Architecture tests

Verify:

```text
contract package imports no MCP, LangChain, LangGraph, or Pi dependencies
runtime core imports no Pi or LangChain packages
consumer adapters contain no native tool business logic
graph adapter does not call MCP adapter directly
Pi extension does not execute shell commands
remote MCP inventory is not automatically trusted
no ServiceFabric MCP server was added
no application runtime or Compose files changed
```

---

# 15. Dependency management

Each new Python package must own its dependencies.

Do not add MCP, LangChain, or LangGraph dependencies to:

```text
universal Flask runtime
existing FastAPI core
servicefabric_contracts
unrelated production images
```

Use exact dependency inputs and committed locks according to the repository’s P0-06 conventions.

The Pi extension must use a committed lockfile.

Do not upgrade unrelated frameworks.

---

# 16. Verification configuration

At the beginning of V1-01, its completion verification may be marked planned.

Before merging, replace it with actual commands covering at least:

```text
existing contract tests
existing V1-00 runtime/client tests
MCP adapter tests
LangChain adapter tests
graph adapter tests
Pi extension tests
cross-consumer integration tests
architecture tests
schema snapshots
dependency-lock validation
TypeScript build/typecheck
git diff check
```

Recommended final logical checks:

```text
v1-01-python-tests
v1-01-pi-tests
v1-01-cross-consumer-tests
schema-snapshots
architecture-guardrails
architecture-tests
dependency-locks
```

Use the actual test directories created by the implementation.

---

# 17. Suggested internal commit sequence

Use logical commits such as:

```text
docs: hand off programme to V1-01
feat: add approved federated MCP client adapter
feat: add research search-papers portfolio resources
feat: add LangChain toolset projection
feat: add composite LangGraph execution
feat: add Pi ServiceFabric extension
feat: add research-demo toolset
test: add cross-consumer integration coverage
ci: make V1-01 completion verification executable
docs: complete V1-01 handoff
```

Do not combine the entire milestone into one undifferentiated commit.

---

# 18. Status updates

Update milestone status after logical phases:

```text
federated-mcp-adapter
langchain-projection
composite-graph-adapter
pi-extension
research-demo-toolset
cross-consumer-verification
```

At V1-01 completion:

```text
v1-00 = completed
v1-01 = completed
v2-00 = current
```

Update:

```text
config/agent/milestones.json
docs/workplans/current.md
docs/workplans/status.json
```

Create the next milestone workplan before completing the handoff, or point to a committed placeholder that is valid under the workplan schema.

---

# 19. Scope prohibitions

Do not:

```text
create a ServiceFabric MCP server
create an MCP gateway
expose all remote MCP tools automatically
trust remote MCP annotations as policy
place credentials in portfolio files
execute arbitrary STDIO commands
add arbitrary shell execution
add arbitrary Python imports
put LangChain into runtime core
put MCP dependencies into contract package
let graphs call execution adapters directly
implement a database registry
implement durable operation persistence
add Django models or migrations
modify Compose or Nginx
modify legacy templates or catalogue loading
build an application factory
add workstation mutation tools
mass-format unrelated files
```

---

# 20. Stop conditions

Stop and report if:

```text
canonical hashes differ
V1-00 is absent from main
V1-00 completion checks fail
a remote MCP tool cannot be explicitly selected
schema normalization cannot be made deterministic
the MCP dependency would leak into contract or runtime core
LangChain projection requires changing canonical semantics
Pi integration requires tool business logic in TypeScript
composite graphs cannot use the canonical client
credentials would need to enter committed configuration
the implementation requires a database or MCP gateway
```

Do not conceal a design conflict behind a permissive fallback.

---

# 21. Acceptance criteria

V1-01 is complete when:

```text
[ ] One MCP-backed canonical tool is explicitly approved and schema pinned.
[ ] Remote MCP inventory is never trusted automatically.
[ ] Schema drift disables the affected tool.
[ ] A LangChain/LangGraph consumer can load a named ServiceFabric toolset.
[ ] A composite graph is exposed as one canonical tool.
[ ] Nested graph calls use the canonical runtime.
[ ] A Pi extension loads and invokes the selected toolset.
[ ] Python, CLI, LangGraph and Pi use the same canonical resources.
[ ] math.calculate remains operational.
[ ] research.search_papers works against a deterministic test MCP provider.
[ ] research.prepare_literature_review works as a composite graph.
[ ] No MCP gateway or ServiceFabric MCP server exists.
[ ] All actual V1-01 completion checks are committed and passing.
[ ] Handoff to V2-00 is generated.
```

---

# 22. Completion report

Report only:

## Starting state

```text
branch
base commit
V1-00 merge commit
working-tree state
```

## Changed areas

```text
MCP client adapter
research tool resources
LangChain integration
LangGraph composite adapter
Pi extension
research-demo toolset
tests
dependency locks
agent milestone configuration
```

## Integration behavior

Explain concisely:

```text
how remote MCP selection works
how schema drift is handled
how LangChain tools invoke ServiceFabric
how graphs make nested calls
how Pi registers and calls tools
```

## Validation

Provide concise pass/fail summaries and test counts.

## Deviations

List deviations from this workplan.

## Known limitations

Explicitly defer:

```text
MCP gateway
application builder
persistent registry
durable operations
production approval engine
sandbox
workstation mutation
```

## Rollback

Normal PR revert. No persistent-data migration should be required.

## Next milestone

```text
V2-00 — Immutable application builder
```

Stop after V1-01.
