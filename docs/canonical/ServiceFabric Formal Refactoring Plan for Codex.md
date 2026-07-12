# ServiceFabric Formal Refactoring Plan for Codex

**Repository:** `chubaz/ServiceFabric-Public`
**Starting revision reviewed:** `b1245e4fc38b0c6ea222ea62986f479dd1fd2eef`
**Execution environment:** Codex launched from the parent **Tool Builder** directory
**Initial scope:** P0 containment and canonical contract package
**Implementation method:** One independently reviewable pull request at a time

---

# 1. Codex operating mandate

Codex must treat this document as an execution plan, not as permission to redesign the platform freely.

For every pull request, Codex must:

1. Read the canonical specifications relevant to that pull request.
2. Read every target file and its direct dependencies.
3. Record the current behaviour through tests before changing it, unless the behaviour is explicitly classified as unsafe and prohibited.
4. Make only the changes assigned to that pull request.
5. Avoid opportunistic framework migrations or formatting rewrites.
6. Update architectural traceability and tests in the same pull request.
7. Report unresolved risks instead of concealing them behind fallbacks.
8. Keep the legacy application surface functional unless the pull request explicitly disables an unsafe feature.
9. Never expose a new capability through MCP during P0.
10. Never create a new execution path that bypasses the future canonical invocation pipeline.

Codex must not merge several planned pull requests into one large change.

---

# 2. Canonical specification inputs

The **Tool Builder** parent folder contains the architectural documents produced during the design sessions.

Codex must locate them by document heading rather than assuming filenames.

Search for these headings:

```text
Canonical ServiceFabric Tool Manifest v1
Tool Capsule Runtime Framework v1
System-Building Graph Specification v1
System-Maintenance Graph Specification v1
System-Evolution Graph Specification v1
ServiceFabric Tool Registry, Capability Discovery, and Routing Specification v1
ServiceFabric Security, Identity, Authorization, Approval, and Side-Effect Governance Framework v1
ServiceFabric Telemetry, Evaluation, and Agent-Callability Testing Framework v1
ServiceFabric Domain Tool Portfolio and Prioritisation Framework v1
ServiceFabric Stage 11 — Reference Implementations
ServiceFabric Production Architecture, Roadmap, and Engineering Standards v1
```

Suggested discovery commands:

```bash
pwd
find .. -maxdepth 4 -type f \
  \( -name "*.md" -o -name "*.txt" -o -name "*.docx" -o -name "*.pdf" \)

rg -l "Canonical ServiceFabric Tool Manifest v1" ..
rg -l "Tool Capsule Runtime Framework v1" ..
rg -l "Production Architecture, Roadmap, and Engineering Standards v1" ..
```

Codex must create a repository-local specification index containing:

* Canonical document title
* Relative path from the repository
* File hash
* Relevant sections
* Pull requests governed by that document

Do not move or rewrite the original documents.

## 2.1 Authority order

When sources conflict, use this order:

```text
1. Current user direction in this plan
2. Security and governance invariants
3. Canonical ServiceFabric specifications
4. Stage 12 production architecture
5. Approved ADRs in the repository
6. Tested current behaviour
7. Existing comments and agent instructions
```

Existing repository comments describe the prototype and may be stale. For example, the current platform documentation assumes Flask dynamic execution and separate Svelte and React build paths.

---

# 3. Corrected platform model

## 3.1 Service package is not the same as a tool

ServiceFabric must support a broader deployable or registrable object:

```text
ServicePackageDefinition
```

A service package may contain:

* A web frontend
* An HTTP API
* A CLI
* A background worker
* A graph
* A library
* A scheduled process
* An externally hosted service
* An external MCP server
* One or more machine-callable tool operations

A `ToolDefinition` represents one bounded operation that an agent or graph may invoke.

## 3.2 MCP is an exposure mechanism

The MCP gateway should not be described as hosting the underlying tool code.

It performs:

```text
Discovery projection
Contract projection
Protocol translation
Authentication boundary
Invocation forwarding
Progress and cancellation projection
Result projection
```

The actual implementation may be:

* Hosted by ServiceFabric
* Run as an isolated CLI process
* Run in a container
* Run through an internal graph
* Hosted externally behind HTTP
* Hosted by another MCP server
* Implemented as a database operation
* Implemented as a human task

MCP exposure is independently configured.

## 3.3 Hosting and exposure axes

The canonical package contracts must keep these independent:

```text
Hosting mode:
    managed_container
    managed_process
    managed_static
    managed_graph
    external_service
    external_mcp
    none

Entrypoint kind:
    http_api
    cli
    web_ui
    worker
    graph
    mcp_server
    library

Exposure:
    internal
    web
    cli
    scheduled
    mcp
    none
```

Examples:

| Package                     | Hosting            | Entrypoint              | MCP exposure     |
| --------------------------- | ------------------ | ----------------------- | ---------------- |
| Calculator capsule          | Managed container  | HTTP/internal operation | Yes              |
| Research CLI                | Managed process    | CLI                     | Optional         |
| Svelte visualization        | Managed static     | Web UI                  | No               |
| External weather API        | External service   | HTTP API                | Optional wrapper |
| Existing MCP provider       | External MCP       | MCP server              | Federated        |
| Batch reconciliation worker | Managed container  | Worker                  | No               |
| Graph-backed investigation  | Managed graph      | Graph                   | Optional         |
| Human-facing admin console  | Managed static/API | Web UI                  | No               |

## 3.4 Rules for frontend-only and CLI-only packages

A frontend-only package:

* Receives a `ServicePackageDefinition`.
* Has a `web_ui` entrypoint.
* Does not require a `ToolDefinition`.
* May consume tool operations provided by other packages.

A CLI-only package:

* Receives a `ServicePackageDefinition`.
* Has a `cli` entrypoint.
* May remain human-operated.
* Receives a `ToolDefinition` only when ServiceFabric wraps a bounded command as a governed operation.

The existing manifests already mix frontend compilation, core-service URLs, WebSockets, vectors, and Python execution assumptions.   The new package contract must separate these concerns rather than reproduce that coupling.

---

# 4. Target repository structure

The first refactoring waves should move toward:

```text
ServiceFabric-Public/
├── docs/
│   ├── architecture/
│   │   ├── specification-map.md
│   │   └── adr/
│   └── refactoring/
│       ├── programme.md
│       ├── debt-register.yaml
│       └── compatibility-matrix.md
│
├── packages/
│   └── servicefabric_contracts/
│       ├── pyproject.toml
│       ├── src/servicefabric_contracts/
│       └── tests/
│
├── schemas/
│   └── servicefabric/
│       └── v1alpha1/
│
├── scripts/
│   ├── architecture/
│   └── contracts/
│
├── tests/
│   ├── architecture/
│   └── integration/
│
├── 2_backend_api/
├── 3_service_templates/
├── 5_core_services/
└── 6_service_catalog/
```

Do not reorganize the existing numbered directories during P0.

---

# 5. Pull-request sequence

## PR P0-00 — Specification traceability and refactoring guardrails

**Branch:** `refactor/p0-00-specification-traceability`

### Objective

Create the controlling documentation, debt register, and CI guardrails before behavioural refactoring starts.

### Create

```text
docs/architecture/specification-map.md
docs/architecture/adr/0001-mcp-is-an-optional-projection.md
docs/architecture/adr/0002-service-package-versus-tool-operation.md
docs/architecture/adr/0003-legacy-flask-strangler-strategy.md
docs/architecture/adr/0004-one-schema-owner-per-table.md
docs/refactoring/programme.md
docs/refactoring/debt-register.yaml
scripts/architecture/check_legacy_patterns.py
tests/architecture/test_repository_boundaries.py
.github/workflows/refactoring-ci.yml
```

### ADR decisions

#### ADR 0001

```text
MCP is an external protocol projection.
The gateway does not define or own tool implementation.
A package may exist without MCP exposure.
```

#### ADR 0002

```text
ServicePackageDefinition describes a hosted or referenced package.
ToolDefinition describes a bounded callable operation.
One package may implement zero, one, or many tools.
```

#### ADR 0003

```text
Existing Flask services form a temporary legacy application host.
No new tools may depend on dynamic Flask execution.
Migration follows a strangler pattern.
```

#### ADR 0004

```text
Each table has one schema owner and one migration system.
Cross-service ORM ownership is prohibited.
```

### Debt register

Record at least:

```yaml
- id: LEGACY-DYNAMIC-IMPORT
  paths:
    - 5_core_services/flask_base/app/services_loader.py
  status: blocked_for_new_use

- id: LEGACY-FLASK-CREATE-ALL
  paths:
    - 5_core_services/flask_base/app/__init__.py
  status: removal_planned

- id: INSECURE-INTERNAL-TOKEN
  paths:
    - 5_core_services/fastapi_base/app/api/dependencies/auth.py
  status: p0

- id: UNAUTHENTICATED-VECTOR-ENDPOINTS
  paths:
    - 5_core_services/fastapi_base/app/api/endpoints/vector.py
  status: p0

- id: UNAUTHENTICATED-RELOAD
  paths:
    - 5_core_services/flask_base/app/routes.py
  status: p0

- id: FALSE-PRODUCTION-PROFILE
  paths:
    - docker-compose.prod.yml
  status: p0
```

### Architecture checks

Initially, the checks may use an explicit debt allowlist. They must prevent new occurrences of:

```text
run_script_for_instance(
db.create_all(
uvicorn ... --reload
manage.py runserver in production files
super-secret-fabric-key
new unauthenticated /_internal routes
new Docker socket mounts
new plaintext token fields
```

### Tests

* Specification map includes every canonical document.
* Every ADR has status and date.
* Every known unsafe pattern is recorded.
* No unrecorded occurrence of a prohibited legacy pattern exists.

### Acceptance criteria

* No runtime behaviour changes.
* CI passes.
* Canonical documents have recorded hashes.
* Future PRs can cite specification IDs and ADRs.

---

## PR P0-01 — FastAPI security containment

**Branch:** `refactor/p0-01-fastapi-containment`

### Objective

Prevent the current FastAPI prototype from serving as an unauthenticated control or data plane.

The current service uses a hard-coded internal token, has unauthenticated vector and WebSocket endpoints, and permits unrestricted credentialed CORS.

### Modify

```text
5_core_services/fastapi_base/app/core/config.py
5_core_services/fastapi_base/app/main.py
5_core_services/fastapi_base/app/api/dependencies/auth.py
5_core_services/fastapi_base/app/api/endpoints/orchestration.py
5_core_services/fastapi_base/app/api/endpoints/vector.py
5_core_services/fastapi_base/app/api/endpoints/websockets.py
5_core_services/fastapi_base/app/services/vector_store.py
5_core_services/fastapi_base/Dockerfile
5_core_services/fastapi_base/requirements.txt
.env.example.dev
.env.example.prod
```

### Create

```text
5_core_services/fastapi_base/app/security/
    __init__.py
    principal.py
    jwt_validator.py

5_core_services/fastapi_base/tests/
    test_auth.py
    test_vector_security.py
    test_websocket_security.py
    test_cors.py
    test_embedding_failure.py
```

### Required implementation

#### Principal context

Create a verified principal type:

```python
class PrincipalContext(BaseModel):
    subject: str
    principal_type: Literal["human", "service"]
    tenant_id: str | None
    issuer: str
    audience: str
    scopes: frozenset[str]
```

#### Token validation

Replace string comparison with JWT validation that verifies:

* Signature
* Issuer
* Audience
* Expiry
* Not-before
* Token type
* Subject
* Tenant where required

Configuration must fail startup in production if required identity settings are absent.

Do not log or return the raw token.

#### Endpoint protection

Require an authenticated principal for:

```text
/orchestration/*
/vector/*
/broadcast
/ws/events/*
```

Authenticate WebSocket connections before calling `accept()`.

#### Vector tenant isolation

The caller must not directly determine a globally shared collection name.

Map:

```text
tenant_id + logical_collection_id
    → internal physical collection identifier
```

Validate:

* Collection identifier format
* Document count
* Document size
* Metadata size
* `top_k` bounds
* ID count consistency

#### Embedding failure

Remove the zero-vector fallback.

Provider failure must produce a typed dependency error. The current code silently creates zero vectors after embedding failures.

#### CORS

Read allowed origins from configuration.

Prohibit:

```text
allow_origins=["*"]
with
allow_credentials=True
```

#### Container runtime

Remove `--reload` from the image command. The existing image enables it unconditionally.

Run as a non-root user.

### Tests

* Missing token rejected.
* Invalid issuer rejected.
* Invalid audience rejected.
* Expired token rejected.
* Tenant A cannot read or delete Tenant B’s vectors.
* WebSocket is not accepted before authentication.
* Broadcast requires service-level authority.
* Token does not appear in logs or audit payloads.
* Embedding failure returns an explicit error.
* Production config rejects wildcard credentialed CORS.
* FastAPI image contains no reload command.

### Out of scope

* MCP
* Tool Registry
* Full OIDC provider integration
* Model gateway
* Vector database replacement

### Acceptance criteria

No FastAPI mutation or retrieval endpoint operates anonymously unless explicitly documented as public health information.

---

## PR P0-02 — Flask execution and reload containment

**Branch:** `refactor/p0-02-flask-execution-containment`

### Objective

Prevent mutable generated code, reload controls, and debug routes from being available in production.

The current loader dynamically imports catalogue code and executes `service.py` inside the Flask application worker.

### Modify

```text
5_core_services/flask_base/app/config.py
5_core_services/flask_base/app/__init__.py
5_core_services/flask_base/app/middleware.py
5_core_services/flask_base/app/routes.py
5_core_services/flask_base/app/services_loader.py
5_core_services/fabric_watcher/watcher.py
docker-compose.yml
docker-compose.dev.yml
docker-compose.prod.yml
.env.example.dev
.env.example.prod
```

### Add configuration

```text
ENABLE_DYNAMIC_SERVICE_IMPORTS
ENABLE_GENERATED_SERVICE_IMPORTS
ENABLE_LEGACY_FAAS_EXECUTION
ENABLE_INTERNAL_RELOAD
ENABLE_DEBUG_ROUTES
```

Defaults:

| Environment |     Dynamic catalogue | Generated code |     FaaS |   Reload |    Debug |
| ----------- | --------------------: | -------------: | -------: | -------: | -------: |
| Development |              Optional |       Optional | Optional | Optional | Optional |
| Test        |              Explicit |             No | Explicit |       No |       No |
| Production  | Static allowlist only |             No |       No |       No |       No |

### Required changes

#### Dynamic loader

* Do not scan `4_generated_services` in production.
* Require an explicit allowlist for any legacy catalogue package loaded in production.
* Validate service names before path construction.
* Do not add arbitrary runtime paths permanently to `sys.path`.
* Fail closed when a prohibited path is requested.

#### FaaS route

`POST /execute/<instance_id>` must:

* Return a stable disabled response when `ENABLE_LEGACY_FAAS_EXECUTION=false`.
* Never execute in production.
* Avoid returning exception details.
* Preserve the route temporarily for compatibility.

#### Reload route

`/_internal/reload` must:

* Be absent or return 404 in production.
* Require authenticated service identity in development if enabled.
* Validate the target against an allowlist.
* Never accept arbitrary external access.

The current route can dynamically register services or signal the parent process without authentication.

#### Debug routes

Remove or environment-gate:

```text
/debug/me
/_debug_environ
```

#### Upload response

Remove internal filesystem paths from API responses.

Add:

* Maximum upload size
* Permitted file-type policy
* Tenant-isolated path resolution
* Filename collision handling

#### Watcher

* Include `fabric_watcher` only in the development profile.
* Add authentication to its reload requests if reload remains enabled.
* Do not describe it as a sandbox or command runner.

### Tests

* Production cannot import generated services.
* Production cannot call the FaaS route.
* Production has no internal reload route.
* Path traversal service names are rejected.
* Public callers cannot reload services.
* Exception messages do not expose paths.
* Upload response does not reveal an internal path.
* Watcher is absent from rendered production Compose configuration.

### Acceptance criteria

No mutable Python code can enter the production Flask process through the service catalogue, generated-services directory, reload endpoint, or FaaS route.

---

## PR P0-03 — Tenant authorization and identity schema correction

**Branch:** `refactor/p0-03-tenant-and-schema-containment`

### Objective

Correct immediate cross-owner and schema mismatches before introducing canonical contracts.

Django uses UUID user IDs, while the Flask model currently maps `owner_id` as an integer and references an undeclared field.

### Modify

```text
2_backend_api/service_fabric/api/views.py
2_backend_api/service_fabric/api/serializers.py
2_backend_api/service_fabric/api/models.py
2_backend_api/service_fabric/myproject/settings.py
5_core_services/flask_base/app/models.py
5_core_services/flask_base/app/middleware.py
```

### Create

```text
2_backend_api/service_fabric/api/permissions.py
2_backend_api/service_fabric/api/tests/test_service_permissions.py
2_backend_api/service_fabric/api/tests/test_cookie_security.py
5_core_services/flask_base/tests/test_schema_parity.py
5_core_services/flask_base/tests/test_token_claims.py
```

### Required changes

#### Object-level authorization

Split read visibility from write ownership.

Rules:

```text
Anonymous:
    read free-tier, non-hidden services only

Authenticated:
    read own services
    read permitted free-tier services

Write, update, delete:
    owner only
    unless an explicit administrative permission exists
```

The current queryset includes all free-tier services for authenticated users while write permissions are available to authenticated users, creating a likely cross-owner mutation path.

Implement an object permission such as:

```python
class IsServiceOwnerForWrite(BasePermission):
    ...
```

#### Flask schema parity

Align:

* `owner_id` as PostgreSQL UUID
* Nullable fields
* `is_free_tier`
* Service status fields actually used by Flask
* UUID parsing for authenticated users

Add a test comparing the mapped Flask columns against the Django-owned table contract.

This is a temporary compatibility mapping, not endorsement of dual ORM ownership.

#### JWT claims

Validate:

* Issuer
* Audience
* Token type
* UUID subject or user identifier

Remove debug printing.

Return safe error messages.

#### Cookies

Set security flags from environment:

```text
secure = true in production
httponly = true
samesite according to deployment model
```

### Acceptance criteria

* Another user cannot modify or delete a free-tier service.
* Flask and Django agree on UUID ownership.
* Invalid audience or issuer is rejected.
* Authentication errors do not expose token internals.

---

## PR P0-04 — Credential containment

**Branch:** `refactor/p0-04-credential-containment`

### Objective

Remove plaintext provider credentials from ordinary Django application fields.

The current `CloudIntegration` model stores OAuth access and refresh tokens as text and notes that encryption remains future work.

### Preflight

Codex must first search all uses:

```bash
rg "CloudIntegration|access_token|refresh_token" \
  2_backend_api 5_core_services 6_service_catalog
```

### Preferred target model

```python
class CloudIntegration(models.Model):
    user = ...
    service = ...
    credential_binding_id = models.UUIDField(...)
    expires_at = ...
    scopes = models.JSONField(...)
    last_synced = ...
```

Raw credentials belong behind:

```python
class CredentialStore(Protocol):
    def put(...)
    def get_lease(...)
    def revoke(...)
```

### Development implementation

A development credential store may use encrypted local storage, but it must:

* Be explicitly development-only
* Require an encryption key from the environment
* Never write raw tokens to logs
* Never expose raw tokens through serializers

### Production behaviour

Production startup must fail or integrations must remain disabled when no approved credential-store backend is configured.

### Migration

* Add credential reference fields.
* Migrate existing values into the configured store.
* Verify migration.
* Clear legacy plaintext fields.
* Remove legacy fields in a later migration after compatibility verification.

### Tests

* Raw token never appears in API serialization.
* Raw token never appears in logs.
* Missing production credential backend fails safely.
* Revoked binding cannot be leased.
* Tenant cannot access another tenant’s binding.

---

## PR P0-05 — Production-profile correction

**Branch:** `refactor/p0-05-production-profile`

### Objective

Make the production profile genuinely production-oriented.

The present production override mounts source and launches Django’s development server.  The base configuration also installs frontend dependencies at service startup and exposes FastAPI directly.

### Modify

```text
docker-compose.yml
docker-compose.dev.yml
docker-compose.prod.yml
Makefile
.env.example.prod

1_proxy/Dockerfile
1_proxy/conf.d/default.conf

2_backend_api/Dockerfile
2_backend_api/entrypoint.sh

5_core_services/flask_base/Dockerfile
5_core_services/fastapi_base/Dockerfile
5_core_services/vite_base/Dockerfile
5_core_services/react_base/Dockerfile
```

### Required production properties

* No `manage.py runserver`
* No `uvicorn --reload`
* No source-code bind mounts
* No `npm install` at startup
* No direct host exposure except the reverse proxy
* No watcher
* No component laboratory
* No generated-services write mount
* Non-root processes
* Pinned base image versions
* Health checks
* Graceful shutdown
* Read-only filesystems where practical
* Explicit writable volumes
* Production secret validation
* No example secret automatically copied over a real environment file

### Frontend assets

Do not delete React in this PR.

Instead:

1. Inventory active Svelte and React applications.
2. Build assets during image build or a controlled build stage.
3. Copy immutable outputs into the serving image or read-only asset volume.
4. Remove runtime builder processes from production.

React retirement requires a later migration report.

### Legacy catalogue

Package the approved legacy catalogue snapshot into the Flask image or mount it read-only from a release artifact.

Production must not read mutable host source directories.

### Makefile

`make prod` must:

* Never overwrite `.env`.
* Validate required configuration.
* Render Compose config.
* Run preflight checks.
* Start only the production profile.

### Tests

```bash
docker compose -f docker-compose.yml \
  -f docker-compose.prod.yml config
```

Automated assertions:

* No `runserver`
* No `--reload`
* No source bind mounts
* No watcher
* No `npm install` command
* No directly published FastAPI, Flask, or Django ports
* All application containers declare non-root users
* Required health checks exist

### Acceptance criteria

The resulting production profile contains immutable runtime artifacts and cannot dynamically introduce source code.

---

# 6. Canonical contract package

## PR C1-00 — Contract package foundation and package-hosting model

**Branch:** `refactor/c1-00-contract-package-foundation`

### Objective

Create the framework-neutral canonical contract package and incorporate heterogeneous ServiceFabric hosting.

### Create

```text
packages/servicefabric_contracts/
├── pyproject.toml
├── README.md
├── src/servicefabric_contracts/
│   ├── __init__.py
│   ├── common.py
│   ├── metadata.py
│   ├── service_package.py
│   ├── entrypoints.py
│   ├── exposure.py
│   ├── artifacts.py
│   └── schema_export.py
└── tests/
    ├── test_service_package.py
    ├── test_entrypoints.py
    ├── test_schema_generation.py
    └── fixtures/

schemas/servicefabric/v1alpha1/
scripts/contracts/export_schemas.py
scripts/contracts/check_schema_snapshots.py
```

### Source-of-truth rule

Use Pydantic v2 models as the Python authoring source and export stable JSON Schema 2020-12 snapshots.

Generated schemas must be committed so other languages do not depend on importing Python.

### Core metadata

```python
class ResourceMetadata(BaseModel):
    id: str
    name: str
    namespace: str | None
    labels: dict[str, str]
    annotations: dict[str, str]
    owner_ref: str
```

### Service package

```python
class ServicePackageDefinition(BaseModel):
    api_version: Literal["servicefabric.ai/v1alpha1"]
    kind: Literal["ServicePackageDefinition"]
    metadata: ResourceMetadata
    spec: ServicePackageSpec
```

Minimum `ServicePackageSpec`:

```text
package identifier
package version
description
artifact reference
hosting mode
entrypoints
declared capabilities
runtime requirements
network policy
storage requirements
health model
ownership
lifecycle
```

### Entrypoints

Support:

```python
EntrypointKind = Literal[
    "http_api",
    "cli",
    "web_ui",
    "worker",
    "graph",
    "mcp_server",
    "library",
]
```

Each entrypoint must define:

* Stable ID
* Kind
* Invocation mode
* Hosting mode
* Runtime reference
* Health behaviour
* Resource limits where managed
* Declared exposures
* Whether it is machine-callable
* Whether it may produce effects

### Exposure

```python
ExposureKind = Literal[
    "internal",
    "web",
    "cli",
    "scheduled",
    "mcp",
    "none",
]
```

MCP exposure must be optional.

### Examples required as fixtures

```text
frontend-only Svelte package
CLI-only financial calculator
managed HTTP tool capsule
externally hosted HTTP provider
federated external MCP server
graph-backed research service
worker-only reconciliation package
```

### Validation invariants

* Frontend-only package may have no ToolDefinition.
* MCP exposure requires a machine-callable operation.
* External packages cannot declare managed container resources.
* CLI entrypoints require a bounded command declaration before machine invocation.
* `none` exposure cannot coexist with public exposure.
* Entrypoint IDs are unique within a package.
* Artifact digests are required for immutable managed packages.
* Secrets are references, never literal values.

### Acceptance criteria

* All fixtures validate.
* Invalid combinations fail.
* JSON schemas are stable and reproducible.
* No Django, Flask, FastAPI, or MCP dependency exists in the contract package.

---

## PR C1-01 — Tool lifecycle contracts

**Branch:** `refactor/c1-01-tool-lifecycle-contracts`

### Objective

Implement operation-level tool contracts from the Canonical Tool Manifest.

### Create

```text
packages/servicefabric_contracts/src/servicefabric_contracts/
    tool_definition.py
    tool_revision.py
    tool_deployment.py
    tool_status.py
    behavior.py
    effects.py
    security.py
    reliability.py
    observability.py
    quality.py
    lifecycle.py
    dependencies.py
    mcp_projection.py

packages/servicefabric_contracts/tests/
    test_tool_definition.py
    test_tool_revision.py
    test_tool_invariants.py
```

### Required resources

```text
ToolDefinition
ToolRevision
ToolDeployment
ToolStatus
```

### Tool implementation reference

A ToolDefinition must reference an execution target independently of MCP:

```python
class ExecutionBinding(BaseModel):
    service_package_id: str | None
    entrypoint_id: str | None
    adapter: ExecutionAdapterKind
    external_ref: str | None
```

Supported adapters:

```text
native_function
native_service
internal_graph
external_http
database_operation
command_runner
federated_mcp
human_task
```

A CLI-backed tool uses:

```text
adapter = command_runner
entrypoint kind = cli
```

A frontend-only package has no corresponding tool unless it also declares a callable operation.

### MCP projection

The MCP section must contain only projection information:

```text
expose
name override
title
description
annotations
structured-result support
task projection policy
```

It must not define implementation endpoints or credentials.

### Invariants

Implement the applicable canonical invariants, including:

* Stable tool IDs
* Immutable revisions
* Input and output schemas
* Declared effects
* Declared permissions
* Declared dependencies
* Valid execution binding
* MCP exposure optional
* No provider secrets
* No mutable deployment data inside ToolRevision

---

## PR C1-02 — Invocation and result contracts

**Branch:** `refactor/c1-02-invocation-contracts`

### Objective

Add the canonical runtime boundary shared by internal calls, MCP projections, CLIs, jobs, and graphs.

### Create

```text
packages/servicefabric_contracts/src/servicefabric_contracts/
    invocation.py
    caller.py
    execution_context.py
    budgets.py
    results.py
    errors.py
    evidence.py
    effects_receipt.py
    operations.py

packages/servicefabric_contracts/tests/
    test_invocation.py
    test_result_envelope.py
    test_error_catalogue.py
    test_effect_receipt.py
```

### Required types

```text
ToolInvocationRequest
CallerContext
ProtocolContext
ParentExecutionContext
ExecutionBudget
ToolExecutionContext
ToolResult
ToolError
EvidenceRecord
ObservedEffect
EffectReceipt
ServiceFabricOperation
```

### Standard result envelope

```json
{
  "status": "success | partial | error",
  "data": {},
  "error": null,
  "warnings": [],
  "evidence": [],
  "meta": {}
}
```

### Error namespaces

```text
SF-AUTHN-*
SF-AUTHZ-*
SF-DELEGATION-*
SF-APPROVAL-*
SF-VALID-*
SF-POLICY-*
SF-BUDGET-*
SF-EXEC-*
SF-DEPEND-*
SF-OUTPUT-*
SF-EFFECT-*
SF-QUALITY-*
SF-MCP-*
SF-RUNTIME-*
```

### Protocol neutrality

The invocation contracts must not import MCP types.

Protocol adapters translate into and out of these contracts.

---

## PR C1-03 — Legacy manifest compatibility translator

**Branch:** `refactor/c1-03-legacy-manifest-translator`

### Objective

Provide a safe migration path from current `fabric-manifest.json` files without treating them as canonical.

### Create

```text
packages/servicefabric_contracts/src/servicefabric_contracts/legacy/
    __init__.py
    fabric_manifest_v0.py
    translator.py
    diagnostics.py

packages/servicefabric_contracts/tests/legacy/
    test_vite_manifest.py
    test_quant_vite_manifest.py
    test_data_science_manifest.py

scripts/contracts/translate_legacy_manifest.py
```

### Behaviour

The translator should:

1. Parse the current manifest.
2. Produce a draft `ServicePackageDefinition`.
3. Record every inferred field.
4. Record every unsupported or ambiguous field.
5. Never automatically publish a ToolDefinition.
6. Never infer side-effect permissions.
7. Never infer MCP exposure.
8. Never convert `service.py` into trusted execution automatically.

Example diagnostic:

```json
{
  "severity": "warning",
  "code": "LEGACY-EXECUTION-ASSUMPTION",
  "field": "rules.compilation[1]",
  "message": "Legacy manifest assumes in-process service.py execution."
}
```

The existing quantitative manifest explicitly assumes Python logic in `service.py` and a shared vector/WebSocket infrastructure.  The translator must expose that assumption rather than silently preserve it.

### Acceptance criteria

* Every current template manifest can be parsed or produces a precise diagnostic.
* Translation creates drafts only.
* No legacy manifest becomes MCP-visible.
* No legacy execution path becomes trusted.

---

## PR C1-04 — Django administrative draft integration

**Branch:** `refactor/c1-04-django-contract-drafts`

### Objective

Allow Django to manage authoring drafts without making Django the runtime registry.

### Create a separate Django app

```text
2_backend_api/service_fabric/tool_authoring/
    __init__.py
    apps.py
    admin.py
    models.py
    serializers.py
    services.py
    migrations/
    tests/
```

Do not add canonical lifecycle blobs to `ServiceInstance`.

### Draft models

```text
ServicePackageDraft
ToolDefinitionDraft
PublicationRequest
```

Store:

* Draft content
* Schema version
* Validation status
* Validation errors
* Author
* Review status
* Content hash
* Creation and modification times

Do not store:

* Live ToolStatus
* Deployment routing
* Provider credentials
* Active policy decisions
* Invocation state

### Services

```python
validate_service_package_draft(...)
validate_tool_definition_draft(...)
export_publication_candidate(...)
```

All validation must call `servicefabric_contracts`.

### Acceptance criteria

* Django can create and validate drafts.
* Invalid drafts cannot enter review.
* No draft becomes active or discoverable.
* `ServiceInstance` remains a legacy application record.
* Runtime services do not read draft tables directly.

---

# 7. Subsequent pull-request map

After P0 and C1 are complete, continue in this order.

## C2 — Registry service

```text
C2-00 Registry database and migrations
C2-01 Immutable revision publication
C2-02 Capability discovery and lifecycle
C2-03 Deployment and status resources
C2-04 Signed publication transaction
```

## C3 — Canonical invocation runtime

Create a new service rather than turning the existing prototype gateway into the final runtime:

```text
5_core_services/invocation_runtime/
```

Pull requests:

```text
C3-00 Runtime skeleton
C3-01 Input and output validation
C3-02 Policy and identity interceptors
C3-03 Budget, deadline, and cancellation
C3-04 Execution adapters
C3-05 Evidence and effect verification
C3-06 Durable operations
```

## C4 — Hosting adapters

```text
C4-00 Managed HTTP service adapter
C4-01 CLI command adapter
C4-02 Static frontend package deployment
C4-03 Background worker adapter
C4-04 Internal graph adapter
C4-05 External HTTP adapter
C4-06 Federated MCP adapter
C4-07 Sandbox execution adapter
```

This is where the heterogeneous hosting requirement becomes operational.

## C5 — MCP gateway

Create separately:

```text
5_core_services/mcp_gateway/
```

It should provide:

```text
tools/list
tools/call
progress
cancellation
optional durable-operation projection
```

It must not host tool implementation code.

## C6 — Reference vertical slices

```text
math.calculate
research.search_papers
project.create_task
```

These validate deterministic, provider-backed, and effectful paths.

---

# 8. Pull-request rules for Codex

## 8.1 Before coding each PR

Codex must report:

```text
Current branch and commit
Specification documents read
Files inspected
Existing tests
Behaviour being preserved
Unsafe behaviour being disabled
Files expected to change
```

## 8.2 During coding

* Add tests with or before behaviour changes.
* Do not alter unrelated generated frontend code.
* Do not mass-format the repository.
* Do not upgrade frameworks unless required by the PR.
* Do not remove React in P0.
* Do not remove Flask in P0.
* Do not add MCP in P0.
* Do not invent canonical fields not supported by the specifications or an ADR.
* Do not silently accept invalid legacy data.
* Do not use permissive fallback values in production.

## 8.3 Required PR description

Every PR description must contain:

```text
Purpose
Canonical specifications used
ADR references
Threat or defect addressed
Files changed
Behaviour before
Behaviour after
Tests
Migration impact
Rollback
Known limitations
Follow-up PRs
```

## 8.4 Commit discipline

Use small commits such as:

```text
test: characterize vector endpoint authorization
refactor: introduce verified principal context
fix: require tenant-bound vector collections
security: remove zero-vector dependency fallback
docs: update P0 debt register
```

Avoid a single “refactor platform” commit.

---

# 9. Programme-level stop conditions

Codex must stop the current PR and report the conflict when:

* A canonical document cannot be located.
* Two canonical documents materially conflict.
* A migration would destroy user data without a verified backup.
* Existing tests demonstrate behaviour incompatible with the assigned ADR.
* A required secret-store backend is unavailable.
* A framework limitation would require bypassing a security invariant.
* The requested change would make a ToolRevision mutable.
* A CLI or frontend package is being incorrectly forced into MCP exposure.
* A production fix depends on retaining dynamic generated-code execution.
* A pull request cannot be rolled back independently.

---

# 10. First-wave completion gate

P0 and C1 are complete only when:

```text
[ ] Canonical specifications are indexed and hashed.
[ ] MCP is documented as optional projection.
[ ] ServicePackageDefinition supports API, CLI, UI, worker, graph, and external services.
[ ] ToolDefinition remains operation-level.
[ ] FastAPI endpoints have verified identity and tenant isolation.
[ ] Flask generated execution is disabled in production.
[ ] Reload and debug endpoints are unavailable in production.
[ ] Cross-owner service writes are prevented.
[ ] UUID ownership is aligned.
[ ] Provider credentials are no longer stored as plaintext.
[ ] Production Compose has no source mounts or reload servers.
[ ] Production does not install dependencies at startup.
[ ] Canonical contract schemas are generated and committed.
[ ] Legacy manifests translate only into non-publishable drafts.
[ ] Django manages drafts, not live runtime status.
[ ] No MCP endpoint has been added prematurely.
```

---

# 11. First Codex instruction

The first Codex session should receive:

```text
Execute PR P0-00 only.

Read the canonical ServiceFabric specifications in the parent Tool Builder
folder. Locate them by heading, record their relative paths and SHA-256
hashes, and create the specification map, four ADRs, refactoring programme,
debt register, architecture checks, and baseline CI described in the formal
refactoring plan.

Do not change runtime behaviour.
Do not edit application code.
Do not begin P0-01.
Before writing files, inspect the repository and report the exact files and
canonical documents you found.
After implementation, run the new architecture tests and provide the proposed
pull-request description.
```

After P0-00 is reviewed, Codex should receive one subsequent PR instruction at a time.
