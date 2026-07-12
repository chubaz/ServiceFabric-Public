# ServiceFabric Fit-for-Purpose Assessment and Stabilisation Program

## 1. Executive verdict

The existing repository is valuable as:

* A product and interface prototype
* A Django administrative foundation
* A catalogue of experimental services
* A source of frontend components
* A demonstration of dynamic service loading

It is **not yet suitable as the execution substrate for the Tool Capsule Runtime, lifecycle graphs, or MCP tool arsenal**.

The most important architectural decision is:

> Do not attach MCP directly to the existing dynamic Flask execution path.

Instead, build the new canonical invocation runtime beside the existing platform, migrate capabilities into it, and progressively reduce the Flask system to a temporary legacy application host.

The platform currently combines Django, Flask, FastAPI, two frontend build systems, dynamic Python imports, runtime table creation, mutable filesystem publication, and several partially implemented security mechanisms. The repository itself describes Django, Flask, FastAPI, Svelte, and React as concurrent architectural elements.

The problem is therefore not simply “too many frameworks.” It is that **execution, schema ownership, publication, identity, and application hosting are not separated into dependable authority boundaries**.

---

# 2. Assessment of the proposed five-step plan

## Step 1 — Store ToolDefinition, ToolRevision, and ToolStatus in Django

**Verdict: right objective, wrong resource model.**

The current Django `ServiceInstance` represents a user-owned application instance. It contains mutable configuration, visibility, lifecycle, routing, and presentation fields. It is not an immutable tool revision or registry record.

Do not add three large JSON blobs to `ServiceInstance`.

Create separate resources:

```text
ToolDefinition
ToolRevision
ToolDeployment
ToolStatus
GraphDefinition
GraphRevision
Operation
IdempotencyRecord
ApprovalRecord
EffectReceipt
```

Recommended ownership:

```text
Django:
    Users
    Human administration
    Tool authoring drafts
    Administrative UI

Registry service:
    Published ToolDefinitions
    Immutable ToolRevisions
    Deployments
    Capability indexes
    Lifecycle relationships

Runtime service:
    Operations
    Idempotency
    Invocation records
    Effect receipts

Maintenance service:
    ToolStatus
    ProviderStatus
    Circuits
    Incidents
```

Django may provide the administrative interface for publishing tools, but the live invocation path should not read mutable Django application records as its runtime contract.

## Step 2 — Move execution to FastAPI and add MCP

**Verdict: correct direction, but FastAPI is not presently a secure runtime.**

The existing FastAPI application currently exposes orchestration, vector, and WebSocket routers; it does not implement the canonical Tool Capsule pipeline or an MCP server.

The current service also has serious security gaps:

* Its internal authentication compares against a hard-coded string, `super-secret-fabric-key`.
* The orchestration endpoint records that token in a background audit event.
* Vector ingest, search, and deletion have no authentication dependency.
* WebSocket connections and the HTTP broadcast endpoint are unauthenticated.
* CORS permits every origin while supporting credentials.
* Its production image starts Uvicorn with `--reload`.

FastAPI should become the basis of the new gateway and invocation runtime, but the existing application should be treated as a prototype and substantially rebuilt.

Also distinguish the transports:

```text
Remote clients:
    MCP Streamable HTTP gateway

Local development:
    Separate stdio MCP host process

Internal services:
    Canonical ServiceFabric invocation API
```

FastAPI does not “provide stdio.” The stdio host should be a separate executable using the same registry and capsule runtime.

## Step 3 — Protect context by enclosing it in immutable XML tags

**Verdict: insufficient and directed at the wrong file.**

`agents_sdk/agent_loader.py` only parses agent markdown files into an `AgentSpec`; it has no `ContextManager` or context pre-hook.

XML delimiters can improve prompt clarity, but they are not a security boundary. Malicious content remains malicious content inside XML.

Implement typed context records:

```typescript
interface ContextItem {
  source: "system" | "user" | "tool" | "external";
  trust: "authoritative" | "verified" | "untrusted";
  contentRef: string;
  permittedInfluence: Array<
    "reasoning" | "tool_arguments"
  >;
}
```

Untrusted content must be unable to influence:

```text
Identity
Authorization
Approval
Tool availability
Tenant
Secrets
Provider selection
Effect limits
Audit policy
```

The runtime, rather than the prompt, must enforce that separation.

## Step 4 — Harden the command runner in `fabric_watcher`

**Verdict: wrong component.**

`fabric_watcher/watcher.py` does not execute commands. It monitors filesystem changes and sends reload requests to Flask, React, or Vite services.

The watcher should become:

```text
Development-only:
    permitted

Production:
    disabled and absent
```

Create a separate sandbox subsystem:

```text
Sandbox Controller
    ↓
Ephemeral execution job
    ↓
Restricted Python or command runtime
    ↓
Scanned output artifacts
    ↓
Execution receipt
```

Its controls must include:

* Non-root process
* Read-only base filesystem
* Ephemeral writable directory
* CPU, memory, process, output, and duration limits
* Network denied by default
* Explicit mounts
* No control-plane credentials
* No Docker socket
* Kill and cleanup guarantees

## Step 5 — Add atomic tool publication to `service_generator.py`

**Verdict: correct requirement, wrong implementation location.**

The current generator:

1. Copies a template directory.
2. Modifies files in place.
3. Creates a `ServiceApp`.
4. Triggers reload requests that may fail while processing continues.

The view then separately creates a `ServiceInstance`.

This is not transactional:

```text
Filesystem copy
    and
ServiceApp creation
    and
ServiceInstance creation
    and
Runtime activation
```

can each succeed or fail independently.

Do not turn this application scaffolder into the tool publication engine.

Create a new publication service:

```text
Draft ToolDefinition
        ↓
Build candidate
        ↓
Tests and evaluations
        ↓
Create immutable artifacts
        ↓
Write registry records and outbox event atomically
        ↓
Deploy candidate
        ↓
Activate only after readiness
```

---

# 3. Critical blockers found in the repository

## 3.1 The production configuration is actually a development configuration

`docker-compose.prod.yml` explicitly mounts source code and runs Django’s development server.

It also starts a Vite development server in `component_lab`.

The base Compose configuration:

* Exposes FastAPI directly on the host
* Mounts FastAPI source code
* Runs `npm install` at container startup
* Maintains both Vite/Svelte and React builders
* Gives the Vite builder an 8 GB memory limit

**Required action:** replace the production Compose definition completely. Production must use built, immutable images without source-code mounts, reload servers, or dependency installation at startup.

## 3.2 Dynamic code executes inside the Flask application process

The Flask loader scans catalogue and generated-service directories, manipulates `sys.path`, imports Python modules dynamically, and registers their blueprints in the live process.

The FaaS execution path dynamically imports `service.py`, instantiates `ServiceRunner`, and executes it inside the Flask worker with the application logger, user context, database connectivity, filesystem, environment variables, and network access.

The directory named `dynamic_sandbox` is not a security sandbox.

This is the most important blocker for the Tool Capsule architecture.

**Required action:** generated or mutable code must never execute inside:

* The gateway
* The registry
* Django
* The legacy Flask host
* A worker containing control-plane credentials

Move all executable tool code into immutable capsule workers or ephemeral sandboxes.

## 3.3 Schema ownership is already inconsistent

Django defines `User.id` as a UUID.

The Flask mapping declares `ServiceInstance.owner_id` as an integer, despite the corresponding Django foreign key pointing to that UUID user. It also declares fields non-null that Django permits to be null, and its `to_dict()` references `is_free_tier` without defining the column.

At startup, Flask imports all dynamic models and calls `db.create_all()`.

This is stronger evidence of architectural fragmentation than the existence of three web frameworks.

**Required action:**

```text
One table → one schema owner → one migration system
```

Recommended physical arrangement:

```text
One PostgreSQL cluster

identity_admin schema:
    owned by Django migrations

registry schema:
    owned by registry service migrations

runtime schema:
    owned by invocation/graph runtime migrations

domain schemas:
    owned by their domain services where necessary
```

Other services consume APIs or generated contract clients, not independent ORM definitions of another service’s tables.

Remove all production `db.create_all()` calls.

## 3.4 Authentication and tenant isolation are incomplete

The Flask JWT decoder checks the signature and expiry but does not validate an issuer, audience, token type, or presence of a valid user identifier. It also prints authentication information and returns underlying token errors to callers.

The internal reload endpoint is unauthenticated and can dynamically load a selected service or send `SIGHUP` to the parent process.

The debug environment endpoint is also public.

There is also a probable object-authorization vulnerability in the Django service viewset. Authenticated users’ querysets contain both their own services and every free-tier service; `IsAuthenticatedOrReadOnly` then permits authenticated writes against objects returned by that queryset. An authenticated user could therefore potentially update or delete a free-tier service belonging to another user. This is an inference from the permission and queryset code and should be tested immediately.

Cloud OAuth access and refresh tokens are stored in ordinary `TextField` columns, with encryption left as a future task.

**Required action:** complete a security-containment release before adding MCP.

## 3.5 The vector service is neither tenant-isolated nor failure-safe

The vector API allows callers to choose arbitrary collection names and perform ingest, search, and deletion without authentication.

The vector service silently substitutes a 768-dimensional zero vector when the external embedding request fails.

This converts provider failure into corrupted-but-apparently-successful data.

Its default persistence directory is under `/app/user_media`, but the FastAPI service does not mount the user-media volume in the base Compose definition, meaning persistence may be container-local.

**Required action:** disable the vector endpoints until authentication, tenant-bound collection IDs, validated embeddings, explicit provider failures, and durable storage are implemented.

## 3.6 Current service publication leaves orphaned and inconsistent state

The generator writes files before it creates database records. Reload failures are logged and ignored.

Deleting a `ServiceInstance` deletes only the database record, while the comments incorrectly state that there are no files to clean up.

The generated application directory and `ServiceApp` can therefore outlive the instance or be left behind after partial failure.

## 3.7 The dependency boundary is too broad

The Flask runtime contains web, AI-agent, search, document, vector, statistical, market-data, and quantitative-analysis dependencies in one environment. It also contains duplicate requirements and many unpinned packages.

The Django and FastAPI requirements are also only partially pinned.

This means every Flask-hosted capability inherits:

* A large attack surface
* Slow builds
* Version conflicts
* High memory consumption
* Coupled upgrade risk
* Unnecessary provider libraries

## 3.8 The proposed `data_science_base` is not yet an execution environment

Its `Dockerfile.template` and `run_script.py` are empty.

Its manifest describes a notebook-like application but does not provide sandboxing, invocation contracts, resource limits, or lifecycle behaviour.

Therefore, standardising immediately on `data_science_base` would standardise on an unfinished template.

---

# 4. Recommended target architecture

```text
                         Human administration
                                  │
                          Django Admin/API
                    users, drafts, ownership, UI
                                  │
                           Publication API
                                  │
                    ┌─────────────▼─────────────┐
                    │   Tool Registry Service   │
                    │ definitions and revisions│
                    └─────────────┬─────────────┘
                                  │
External MCP clients ──► MCP Gateway / FastAPI Invocation Runtime
                                  │
                     canonical interceptor pipeline
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
      Native capsules       Graph-backed tools    Sandbox jobs
             │                    │                    │
      Provider gateway       Internal tools       Isolated code
             │
       External systems

Legacy browser applications
             │
       Legacy Flask Host
       existing blueprints only
       no new tools
       no generated-code execution
```

## 4.1 Django’s future role

Keep Django for:

* Users and human identity administration
* Administrative workflows
* Tool-authoring forms
* Review queues
* Approval interfaces
* Operational dashboards

Remove it from:

* Live tool invocation
* Runtime routing
* Provider selection
* Per-call policy evaluation
* ToolStatus ownership
* Dynamic code activation

## 4.2 FastAPI’s future role

Create a new FastAPI runtime rather than incrementally adding MCP routes to the current gateway.

It should contain:

```text
MCP adapter
Canonical invocation API
Revision resolver
Interceptor pipeline
Execution router
Durable-operation API
Cancellation and progress
```

Domain and provider behaviour belongs in capsule packages or workers, not gateway routes.

## 4.3 Flask’s future role

Use a strangler migration:

```text
Current Flask:
    Legacy application host

New FastAPI runtime:
    All new tools and graphs

Migration:
    Move one bounded capability at a time

End state:
    Flask removed or retained only for a small legacy UI surface
```

Do not attempt to convert every existing Flask mini-application before the new runtime exists.

## 4.4 Frontend standardisation

Svelte 5 can become the preferred frontend standard, but removal of React should follow a catalogue inventory and migration report.

The repository currently maintains separate Svelte/Vite and React dependency trees with different Vite and Tailwind versions.

Use:

```text
Svelte workspace:
    Operator console
    Administrative interfaces
    Tool-specific interactive views

Python capsule images:
    Computation and domain execution
```

A UI template and an execution environment are separate concepts.

---

# 5. Refactoring sequence

## Phase A — Containment

Complete before tool or MCP expansion.

1. Replace the production Compose configuration.
2. Remove direct host exposure of FastAPI and Django.
3. Remove `--reload`, source mounts, and runtime `npm install`.
4. Disable unauthenticated vector, WebSocket, reload, and debug endpoints.
5. Replace the hard-coded FastAPI secret.
6. Stop logging credentials and tokens.
7. Set secure cookies according to environment.
8. Encrypt or externalise cloud credentials.
9. Fix free-tier object permissions.
10. Disable generated-code execution in production.
11. Remove the watcher from production.
12. Align UUID ownership types immediately.

**Exit gate:** no known unauthenticated state mutation, cross-owner mutation, plaintext provider credential, or same-process generated-code execution.

## Phase B — Characterisation and safety net

Before structural migration, preserve the behaviour that matters.

Create tests for:

```text
Authentication
Service creation
Service listing
Service deletion
Existing application routing
Dynamic service execution
Template generation
Frontend build
File upload
Vector ingest/search
```

Add:

* Unit tests
* Integration tests
* End-to-end smoke tests
* Tenant-isolation tests
* Security regression tests
* Basic load tests
* Architecture dependency tests

Document which current behaviours are:

```text
Preserve
Replace
Deprecate
Remove
```

**Exit gate:** every legacy path has an explicit disposition and a test or approved removal decision.

## Phase C — Canonical contracts

Add a framework-neutral contracts package:

```text
ToolDefinition
ToolRevision
ToolDeployment
ToolStatus
ToolInvocationRequest
ToolResult
ToolError
EvidenceRecord
EffectReceipt
GraphDefinition
GraphState
```

Generate:

* Pydantic models
* JSON Schemas
* Django form adapters where required
* TypeScript clients
* Database compatibility tests

**Exit gate:** the same serialized contract validates identically in gateway, registry, capsule, and tests.

## Phase D — Data ownership separation

1. Fix current UUID and nullability mismatches.
2. Stop Flask from mapping Django tables as an independent ORM model.
3. Remove `db.create_all()` from startup.
4. Introduce separate database schemas and roles.
5. Add explicit migrations for registry and runtime resources.
6. Replace cross-service ORM access with APIs or generated clients.

**Exit gate:** exactly one migration authority exists for each table.

## Phase E — Invocation runtime

Implement the canonical pipeline in a new service:

```text
Accept request
Resolve revision
Verify identity
Evaluate authorization
Classify effects
Verify approval
Validate input
Reserve idempotency
Establish budgets
Maintenance preflight
Select adapter
Execute
Recover or fall back
Validate output
Verify evidence
Verify effects
Commit result
Emit audit and telemetry
Project protocol response
```

No adapter should be callable except through this pipeline.

**Exit gate:** `math.calculate` can be invoked only through the pipeline, and tests prove that input validation, policy, cancellation, budgets, and output validation cannot be bypassed.

## Phase F — Immutable registry and publication

Create:

```text
Draft
    ↓
Candidate build
    ↓
Tests and evaluation
    ↓
Signed immutable ToolRevision
    ↓
Transactional registry publication
    ↓
Deployment
    ↓
Readiness
    ↓
Activation
```

Use a transactional outbox rather than trying to make PostgreSQL and filesystem operations one database transaction.

**Exit gate:** a failed build, evaluation, artifact upload, or deployment never produces a discoverable active revision.

## Phase G — Execution isolation

Create three worker profiles:

```text
deterministic-python
    Small, pinned, no network by default

domain-python
    Finance, data, document, or research dependencies

sandbox
    Ephemeral execution of untrusted or generated work
```

Do not recreate the current universal Flask dependency environment.

**Exit gate:** a compromised capsule cannot access registry credentials, other tenants’ data, the Docker socket, or undeclared provider endpoints.

## Phase H — MCP adapter

Only after the invocation API is stable:

1. Add `tools/list` from the authorization-aware registry.
2. Add `tools/call` as a projection of the canonical invocation API.
3. Support cancellation and progress.
4. Add local stdio as a separate host executable.
5. Add protocol conformance tests.
6. Ensure the MCP layer contains no tool business logic.
7. Validate token issuer and audience.
8. Never pass client bearer tokens to providers.

**Exit gate:** MCP and internal invocations produce the same canonical result for the same resolved revision.

## Phase I — Vertical slices

Migrate in this order:

```text
1. math.calculate
2. research.search_papers
3. project.create_task
```

They prove respectively:

* Deterministic execution
* Provider and agent-backed retrieval
* Approval, idempotency, persistent effect, and verification

## Phase J — Legacy retirement

After new vertical slices are stable:

* Stop creating new Flask services.
* Migrate useful Flask applications.
* Remove React after active consumers are migrated.
* Remove mutable runtime service loading.
* Remove filesystem publication.
* Remove duplicate builders.
* Retire unused templates and packages.

---

# 6. Fit-for-purpose release gates

The platform should not be declared fit for the tool arsenal until all of these gates pass.

## Security gate

```text
[ ] No hard-coded credentials
[ ] No plaintext OAuth tokens
[ ] No unauthenticated mutation endpoints
[ ] Tenant isolation tests pass
[ ] Token issuer and audience validated
[ ] No dynamic code inside gateway or application host
[ ] Sandboxes deny undeclared network and filesystem access
[ ] Tool outputs cannot grant authority
[ ] Approval binding tested
[ ] Effect verification tested
```

## Architecture gate

```text
[ ] One schema owner per table
[ ] No startup db.create_all()
[ ] Immutable ToolRevisions
[ ] Separate ToolStatus
[ ] Canonical invocation pipeline
[ ] All adapters reachable only through pipeline
[ ] Flask classified as legacy only
[ ] MCP isolated at protocol boundary
```

## Reliability gate

```text
[ ] Worker restart does not lose durable graph state
[ ] Duplicate delivery does not duplicate effects
[ ] Provider timeout produces controlled recovery
[ ] Timeout after commit enters reconciliation
[ ] Registry outage behaviour is defined
[ ] Policy outage fails closed
[ ] Database restoration has been demonstrated
```

## Quality gate

```text
[ ] Unit and contract tests
[ ] Integration tests
[ ] Security tests
[ ] Agent-callability tests
[ ] MCP conformance tests
[ ] Historical failure regression tests
[ ] Canary and rollback procedures
```

## Operational gate

```text
[ ] OpenTelemetry trace per invocation
[ ] Stable error catalogue
[ ] Tool and provider dashboards
[ ] SLOs and alerts
[ ] Named owners
[ ] Runbooks
[ ] Incident-to-evaluation workflow
```

## Supply-chain gate

```text
[ ] Locked dependencies
[ ] No dependency installation at runtime startup
[ ] Images pinned by digest
[ ] SBOMs
[ ] Vulnerability scanning
[ ] Signed artifacts
[ ] Build provenance
[ ] Protected production promotion
```

---

# 7. Corrected immediate backlog

The first repository issues should be created in approximately this order:

```text
P0  Replace false production Compose configuration
P0  Close unauthenticated FastAPI vector and WebSocket endpoints
P0  Remove hard-coded internal token and token logging
P0  Protect or remove Flask reload and debug endpoints
P0  Fix ServiceInstance owner UUID mapping
P0  Fix free-tier object-level write authorization
P0  Remove plaintext cloud credentials
P0  Disable dynamic service execution in production

P1  Add repository CI and baseline tests
P1  Introduce canonical contracts package
P1  Establish one schema owner per database table
P1  Remove Flask db.create_all()
P1  Create registry and runtime database schemas
P1  Implement ToolInvocationPipeline skeleton
P1  Implement immutable publication workflow

P2  Create deterministic Python capsule image
P2  Create dedicated sandbox controller
P2  Implement math.calculate vertical slice
P2  Add OpenTelemetry
P2  Add MCP Streamable HTTP adapter
P2  Add local stdio host

P3  Migrate research.search_papers
P3  Add approval and effect ledger
P3  Migrate project.create_task
P3  Begin legacy Flask application migration
```

---

# 8. Final recommendation

Your core strategic direction should be retained:

```text
Django:
    human control plane

FastAPI:
    canonical runtime and MCP boundary

Svelte:
    preferred interactive frontend

Isolated Python capsules:
    deterministic, finance, data, and agent-backed execution
```

But the safe migration strategy is not:

```text
Replace Flask everywhere
then add MCP
```

It is:

```text
Contain the existing system
        ↓
Characterise and test it
        ↓
Build a clean canonical runtime beside it
        ↓
Route all new tools through that runtime
        ↓
Migrate useful legacy capabilities
        ↓
Retire dynamic Flask execution
```

The single most important program rule should be:

> No new tool may depend on `run_script_for_instance`, dynamic blueprint loading, `db.create_all()`, mutable catalogue files, or the current FastAPI authentication mechanism.

With that rule enforced, the tool arsenal and MCP infrastructure can be built in parallel with legacy-system simplification without inheriting the existing architectural fragmentation.
