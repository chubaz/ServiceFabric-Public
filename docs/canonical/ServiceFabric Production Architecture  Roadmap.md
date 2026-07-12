# ServiceFabric Production Architecture, Roadmap, and Engineering Standards v1

**Status:** Production architecture baseline
**Roadmap stage:** 12 of 12
**API version:** `servicefabric.ai/v1alpha1`
**MCP production profile:** `2025-11-25`
**Primary objective:** Move ServiceFabric from reference implementation to an operable, secure, evolvable production platform.

---

# 1. Executive architectural decisions

The recommended reference architecture adopts the following decisions.

| Area                            | Decision                                         |
| ------------------------------- | ------------------------------------------------ |
| External agent protocol         | MCP over Streamable HTTP                         |
| Local development protocol      | MCP over stdio                                   |
| Canonical internal contract     | ServiceFabric-native JSON Schema contracts       |
| Orchestration                   | Durable ServiceFabric graph runtime              |
| Production scheduler            | Kubernetes                                       |
| Primary transactional store     | PostgreSQL                                       |
| Artifact and evidence store     | S3-compatible object storage                     |
| Event transport                 | NATS JetStream or equivalent durable event bus   |
| Cache                           | Redis, non-authoritative                         |
| Secrets                         | External secrets manager                         |
| Observability                   | OpenTelemetry                                    |
| Container format                | OCI images                                       |
| Supply-chain standard           | SLSA 1.2-aligned provenance                      |
| Artifact signing                | Sigstore Cosign                                  |
| Primary control-plane language  | TypeScript                                       |
| Domain and quantitative workers | TypeScript or Python                             |
| Initial production geography    | Single region, multiple availability zones       |
| Disaster recovery               | Asynchronous secondary region                    |
| Active-active multi-region      | Deferred until justified                         |
| Service mesh                    | Deferred unless operational evidence requires it |
| Kubernetes operator             | Deferred until resource lifecycle stabilizes     |

MCP `2025-11-25` remains the current released production profile as of July 11, 2026. MCP-specific code should remain confined to gateway and projection packages so protocol evolution does not alter internal ServiceFabric contracts.

---

# 2. Production design principles

## 2.1 Separate semantics from deployment

A tool is defined by:

```text
ToolDefinition
ToolRevision
MaintenanceGraph
PolicyBundle
EvaluationSuite
```

It is not defined by:

```text
Container
Pod
Endpoint
Cloud region
Provider
Model
```

Deployment resources implement a revision but do not determine its meaning.

## 2.2 Separate control plane from execution plane

The control plane manages:

* Tool contracts
* Revisions
* Policies
* approvals
* deployments
* health
* evaluations
* lifecycle state

The execution plane performs:

* Tool calls
* Graph-node execution
* Provider calls
* Model calls
* Sandboxed code
* Effect verification

A compromised execution worker should not be able to publish a new revision or alter its governing policy.

## 2.3 Immutable revisions, mutable status

```text
Immutable:
    ToolRevision
    GraphRevision
    PolicyBundle version
    EvaluationSuite version
    Container digest

Mutable:
    ToolStatus
    DeploymentStatus
    ProviderStatus
    IncidentStatus
    Canary traffic
```

## 2.4 At-least-once infrastructure, effectively-once effects

Distributed queues and workers should be assumed to deliver work at least once.

ServiceFabric obtains effectively-once external effects through:

* Idempotency keys
* Argument hashes
* Approval bindings
* Provider references
* Read-after-write verification
* Reconciliation

## 2.5 Fail safely, not uniformly

Different failures require different behaviour.

```text
Authorization unavailable
    Fail closed.

Approval unavailable
    Fail closed.

Registry temporarily unavailable
    Low-risk calls may use a valid signed resolution cache.

Telemetry backend unavailable
    Continue low-risk execution while buffering telemetry.

Critical audit store unavailable
    Block high-risk effects.

Optional ranking model unavailable
    Use deterministic fallback.
```

---

# 3. Logical architecture

ServiceFabric should be divided into four operational planes.

```text
┌─────────────────────────────────────────────────────────────┐
│                      Access plane                           │
│  MCP Gateway · REST Gateway · Operator Console · CLI       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                     Control plane                           │
│ Registry · Policy · Authority · Approval · Lifecycle       │
│ Deployment · Evaluation · Quality · Administration         │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Execution plane                          │
│ Invocation Runtime · Graph Runtime · Capsule Workers       │
│ Model Gateway · Provider Adapters · Sandbox Runners        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│             Observability and evidence plane                │
│ OTel Collectors · Metrics · Traces · Logs · Audit          │
│ Effect Ledger · Evidence Store · Cost Ledger · Incidents   │
└─────────────────────────────────────────────────────────────┘
```

---

# 4. Production topology

```text
External clients and agent frameworks
              │
         Load balancer
              │
      ServiceFabric MCP Gateway
              │
    Authentication and rate control
              │
      Canonical Invocation API
              │
  ┌───────────┼────────────────────┐
  │           │                    │
Tool       Graph               Durable
Runtime    Runtime              Operation API
  │           │                    │
  └───────────┼────────────────────┘
              │
        Execution Router
  ┌───────────┼────────────────────────────┐
  │           │             │              │
Shared     Dedicated      Sandbox       Federated
capsule    capsule        worker        MCP adapter
workers    services       pools         workers
  │           │             │              │
  └───────────┼─────────────┼──────────────┘
              │
      Provider and model gateways
              │
 External APIs · Models · Databases · Enterprise systems
```

Control services run separately:

```text
Tool Registry
Policy and Authority Service
Approval Service
Deployment Controller
Maintenance Controller
Evaluation Service
Lifecycle Graph Runtime
Artifact and Attestation Service
Operations API
```

---

# 5. Service boundaries

## 5.1 MCP Gateway

Responsibilities:

* MCP lifecycle and capability negotiation
* Authentication
* Session correlation
* Authorization context construction
* Caller-specific `tools/list`
* `tools/call` translation
* Progress and cancellation projection
* MCP error projection
* Rate limits
* Request-size limits

It must not:

* Implement domain tools
* Select providers
* Contain business policy
* Store secrets
* Perform retries of external effects

MCP tasks remain experimental in the released specification. ServiceFabric should therefore maintain its own durable operation model and expose MCP task projections only for compatible clients.

## 5.2 Tool Registry

Responsibilities:

* ToolDefinition storage
* Immutable revision storage
* Capability indexing
* Contract retrieval
* Caller-specific discovery
* Version resolution
* Deployment resolution
* Replacement and deprecation relationships

Authoritative database:

```text
PostgreSQL
```

Derived indexes:

```text
Full-text search
Semantic embeddings
Capability relationship graph
```

The initial semantic index should use PostgreSQL with `pgvector` or an equivalent embedded index rather than introducing a separate vector database prematurely.

## 5.3 Policy and Authority Service

Responsibilities:

* Principal verification
* Capability grants
* Delegation attenuation
* Policy decisions
* Tenant constraints
* Resource relationships
* Effect limits
* Signed policy bindings
* Revocation

This service must remain independent of model reasoning.

## 5.4 Approval Service

Responsibilities:

* Action previews
* Approver resolution
* Authentication-strength requirements
* Approval collection
* Preview-hash binding
* Single-use approval consumption
* Expiry and revocation
* Dual-control workflows

Approval records are authoritative transactional data.

## 5.5 Invocation Runtime

Responsibilities:

* Resolve exact revision
* Validate input
* Check policy and approval
* Establish timeout and budgets
* Invoke maintenance graph
* Select execution adapter
* Validate output
* Produce canonical result
* Record audit and telemetry

This is the only ordinary entry point to Tool Capsule execution.

## 5.6 Graph Runtime

Responsibilities:

* Execute graph definitions
* Persist graph state
* Schedule runnable nodes
* Enforce graph budgets
* Invoke tools and subgraphs
* Suspend for approval or human input
* Resume durable operations
* Enforce stopping conditions
* Record routes and decisions

Graph state must never exist only in worker memory.

## 5.7 Capsule Workers

Capsule workers host:

* Native function tools
* Shared domain adapters
* Deterministic transformation tools
* Provider-specific code
* Maintenance hooks

Workers should be replaceable and stateless except for explicitly declared local ephemeral state.

## 5.8 Model Gateway

Responsibilities:

* Approved model configuration
* Provider routing
* Data-classification checks
* Token limits
* Cost limits
* Request redaction
* Structured-output validation
* Model telemetry
* Provider fallback
* Model-configuration versioning

Tools and graphs call a ServiceFabric model configuration, not a raw model endpoint.

## 5.9 Provider Adapter Gateway

Responsibilities:

* Provider-specific authentication
* Network egress policy
* Rate limits
* Retry policy
* Contract normalization
* Provider request identifiers
* Credential exchange
* Schema-drift detection
* Cost measurement

## 5.10 Sandbox Service

Responsibilities:

* Python and command execution
* Ephemeral filesystems
* Resource limits
* Network isolation
* Dependency allowlists
* Artifact export
* Process termination
* Execution receipts

Each sandbox execution should run in a new isolated workload.

## 5.11 Maintenance Controller

Responsibilities:

* Health probes
* Provider health
* Circuit breakers
* ToolStatus
* Degradation policies
* Incident creation
* Quarantine
* Recovery verification
* Evolution signals

## 5.12 Evaluation Service

Responsibilities:

* Suite registry
* Dataset registry
* Evaluation scheduling
* Fixture provisioning
* Historical replay
* Shadow execution
* Scoring
* Reports
* Publication gates
* Canary comparisons

## 5.13 Artifact and Attestation Service

Responsibilities:

* ToolRevision bundles
* Graph bundles
* Test reports
* Evaluation reports
* SBOMs
* Provenance
* Signatures
* Documentation
* Evidence artifacts

---

# 6. Recommended implementation map

| Service               | Initial language           | Deployment                  |
| --------------------- | -------------------------- | --------------------------- |
| MCP Gateway           | TypeScript                 | Kubernetes Deployment       |
| Registry API          | TypeScript                 | Kubernetes Deployment       |
| Policy service        | TypeScript                 | Kubernetes Deployment       |
| Approval service      | TypeScript                 | Kubernetes Deployment       |
| Invocation runtime    | TypeScript                 | Kubernetes Deployment       |
| Graph runtime API     | TypeScript                 | Kubernetes Deployment       |
| Graph workers         | TypeScript/Python          | Kubernetes Deployment       |
| Lifecycle controllers | TypeScript                 | Kubernetes Deployment       |
| Evaluation workers    | TypeScript/Python          | Kubernetes Jobs/workers     |
| Sandbox controller    | TypeScript                 | Kubernetes Deployment       |
| Sandbox executions    | Python/other               | Kubernetes Jobs             |
| Model gateway         | TypeScript                 | Kubernetes Deployment       |
| Provider adapters     | TypeScript/Python          | Shared or dedicated workers |
| Operations API        | TypeScript                 | Kubernetes Deployment       |
| Operator console      | TypeScript web application | Kubernetes Deployment       |

Kubernetes Deployments are appropriate for continuously running stateless services, while Jobs are appropriate for finite executions such as evaluation runs, builds, migrations, and isolated code tasks. Kubernetes also provides startup, readiness, and liveness probes to distinguish initialization, traffic readiness, and runtime failure.

---

# 7. Deployment profiles for Tool Capsules

## 7.1 Shared runtime

Use for:

* Deterministic tools
* Low-risk reads
* Small dependencies
* Moderate traffic
* Similar resource requirements

Examples:

```text
math.calculate
dates.calculate
units.convert
data.validate
```

Benefits:

* Low operational overhead
* Fast startup
* Efficient resource use

Constraints:

* Strong module isolation
* Per-invocation budgets
* No unrestricted native extensions
* No persistent local state

## 7.2 Dedicated capsule service

Use for:

* High traffic
* Heavy dependencies
* Independent scaling
* Specialized runtime
* Stronger fault isolation
* Sensitive provider credentials

Examples:

```text
research.search_papers
finance.retrieve_market_data
documents.extract_tables
```

## 7.3 Graph-backed capsule

Use when a public tool is implemented by a bounded internal graph.

Examples:

```text
research.build_evidence_set
finance.build_company_dataset
software.investigate_failure
```

## 7.4 Sandboxed execution

Use for:

* Generated code
* Arbitrary documents
* Build commands
* Security scanners
* Untrusted files

Each call creates an isolated job or microVM-class execution environment.

## 7.5 Federated MCP capsule

Use for reviewed external MCP servers.

```text
ServiceFabric public contract
        ↓
Federation maintenance graph
        ↓
External MCP client adapter
        ↓
External MCP server
```

External tool definitions must not bypass ServiceFabric policy, telemetry, schema validation, or effect classification.

---

# 8. Synchronous and durable execution

## 8.1 Synchronous path

Use when execution is expected to complete within the gateway request deadline.

```text
MCP call
  ↓
Invocation runtime
  ↓
Capsule
  ↓
ToolResult
```

Suitable for:

* Calculation
* Simple retrieval
* Data validation
* Short provider calls

## 8.2 Durable operation path

Use when work may:

* Exceed an ordinary request deadline
* Wait for human approval
* Wait for external state
* Execute many graph nodes
* Require reconciliation
* Survive worker restarts

```text
Request accepted
       ↓
ServiceFabricOperation created
       ↓
Work item published
       ↓
Durable graph worker executes
       ↓
State committed after each node
       ↓
Result stored
       ↓
Client polls or receives protocol projection
```

## 8.3 Persistence rule

Before acknowledging a durable transition:

```text
State update
Event publication intention
Audit reference
```

must be committed together.

Use a transactional outbox:

```text
PostgreSQL transaction:
    update operation state
    insert outbox event

Event relay:
    publish event
    mark outbox record delivered
```

Consumers use an inbox or processed-event ledger to prevent duplicate effects.

---

# 9. Data architecture

## 9.1 PostgreSQL

PostgreSQL should be the initial authoritative store for:

* Tool definitions
* Tool revisions and lifecycle state
* Graph definitions and runs
* Operations
* Idempotency records
* Policy metadata
* Authority grants
* Approvals
* ToolStatus
* Incidents
* Evaluation metadata
* Deployment records
* Outbox and inbox records
* Cost attribution metadata

Recommended logical schemas:

```text
registry
governance
runtime
operations
evaluations
deployments
audit_index
```

High-volume telemetry should not be stored in the primary transactional cluster.

## 9.2 Object storage

Use for:

* Revision bundles
* Source archives
* Evaluation datasets
* Provider fixtures
* Evidence documents
* Large tool results
* SBOMs
* Provenance
* Build logs
* Audit evidence
* Long-term archives

Every object should have:

* Content hash
* Tenant
* Classification
* Retention policy
* Encryption metadata
* Producing revision
* Access-policy reference

## 9.3 Event bus

Use for:

* Durable operation work
* Maintenance events
* Lifecycle events
* Tool catalogue changes
* Evaluation tasks
* Evolution signals
* Incident notifications
* Deployment events

Recommended initial choice:

```text
NATS JetStream
```

Reasons for the reference design:

* Lower operational footprint than a large streaming platform
* Durable consumers
* Request/reply and event messaging
* Appropriate for command and lifecycle events

Kafka or a managed equivalent becomes appropriate when:

* Event replay becomes a major product capability
* Very large ordered streams are required
* Cross-organization analytics depend on the event log
* Sustained throughput justifies additional complexity

## 9.4 Redis

Redis may support:

* Short-lived registry cache
* Rate limits
* Distributed locks with bounded leases
* Tool-card caching
* Provider-health caching
* Ephemeral coordination

Redis must not be the only store for:

* Approval
* Authority
* Idempotency
* Graph state
* Effect receipts
* Tool revision metadata

## 9.5 Secrets manager

Store:

* Provider credentials
* Database credentials
* Signing configuration
* Encryption keys
* OAuth client credentials
* Tenant-specific secrets

Applications receive short-lived or mounted references rather than unrestricted vault access.

## 9.6 Audit and effect ledger

Critical governance records require append-oriented, integrity-protected storage.

The relational database may index these records, while canonical evidence is written to protected object storage or a dedicated ledger-compatible store.

---

# 10. Reference production invocation

```text
1. Client opens MCP connection.
2. Gateway authenticates client.
3. Gateway creates caller context.
4. Client requests tools/list.
5. Registry returns authorization-filtered projection.
6. Client invokes a tool.
7. Gateway validates protocol request.
8. Registry resolves exact revision and deployment.
9. Policy service evaluates arguments, targets, and effects.
10. Approval service verifies approval where required.
11. Invocation runtime reserves idempotency record.
12. Maintenance graph performs preflight.
13. Execution router selects capsule deployment.
14. Capsule invokes approved providers or models.
15. Output is normalized and schema-validated.
16. Evidence is verified.
17. Effects are verified or reconciled.
18. Result and audit records are committed.
19. Telemetry is emitted.
20. MCP result is projected to the client.
```

The revision selected in step 8 remains fixed for the entire invocation.

---

# 11. Kubernetes deployment architecture

## 11.1 Namespaces

Recommended separation:

```text
servicefabric-gateway
servicefabric-control
servicefabric-runtime
servicefabric-sandboxes
servicefabric-observability
servicefabric-evaluation
servicefabric-system
```

High-risk sandboxes should use dedicated:

* Node pools
* Service accounts
* Network policies
* Pod security controls
* Resource quotas

## 11.2 Workload health

Every long-running service exposes:

```text
/startup
/health/live
/health/ready
```

Definitions:

```text
Startup:
    Has initialization completed?

Liveness:
    Is the process capable of progressing?

Readiness:
    Can this instance safely accept new work?
```

Readiness should fail when:

* Required policy resources are unavailable
* Database connectivity is lost
* Required schema version is incompatible
* The worker is draining
* A critical configuration cannot be loaded

Liveness should not fail because one external provider is unavailable.

## 11.3 Resource controls

Every workload declares:

* CPU request and limit
* Memory request and limit
* Ephemeral-storage limit
* Maximum execution duration
* Pod disruption policy
* Priority class where needed

## 11.4 Autoscaling

Scale by the metric appropriate to each workload.

| Workload           | Primary scale signal                    |
| ------------------ | --------------------------------------- |
| MCP Gateway        | Concurrent connections and request rate |
| Invocation runtime | Active invocations                      |
| Graph workers      | Runnable graph-node queue depth         |
| Evaluation workers | Evaluation queue depth                  |
| Provider adapters  | Provider concurrency and quota          |
| Sandbox workers    | Pending sandbox executions              |
| Model gateway      | Active model requests and token rate    |

CPU should be a secondary rather than universal scaling signal.

---

# 12. Availability and resilience

## 12.1 Initial production target

Deploy one production region across at least three availability zones where the infrastructure provider permits it.

Components requiring high availability:

* MCP Gateway
* Registry
* Policy service
* Approval service
* Invocation runtime
* Graph scheduler
* PostgreSQL
* Event bus
* Secrets access
* Critical telemetry and audit path

## 12.2 Database resilience

Recommended:

* Managed PostgreSQL
* Multi-zone primary
* Point-in-time recovery
* Encrypted backups
* Automated restoration tests
* Read replicas for reporting where useful
* Schema migrations separated from application startup

## 12.3 Degraded modes

| Dependency failure                | Permitted behaviour                   |
| --------------------------------- | ------------------------------------- |
| Semantic index unavailable        | Exact and lexical discovery           |
| Optional model unavailable        | Deterministic fallback                |
| One research provider unavailable | Partial result or fallback            |
| Redis unavailable                 | Bypass cache                          |
| OTel export unavailable           | Buffer or sample locally              |
| Registry unavailable              | Valid signed cache for low-risk calls |
| Policy unavailable                | Deny new calls                        |
| Approval unavailable              | Deny approval-sensitive effects       |
| Audit evidence unavailable        | Deny high-risk effects                |
| Event bus unavailable             | Reject new durable operations         |

## 12.4 Disaster recovery

Initial DR model:

```text
Primary region:
    active

Secondary region:
    warm infrastructure
    replicated artifacts
    restored or replicated database
    replicated configuration
```

Recovery must be tested through scheduled exercises, not inferred from successful backups.

## 12.5 Multi-region policy

Do not introduce active-active execution until ServiceFabric has explicit solutions for:

* Globally unique idempotency
* Approval consistency
* Policy replication
* Tool catalogue consistency
* Effect reconciliation
* Data residency
* Provider-region differences
* Cross-region graph ownership

---

# 13. Network and tenant security

## 13.1 Default network posture

```text
Deny all east-west traffic
Deny all egress
Permit explicit service-to-service routes
Permit explicit provider destinations
```

## 13.2 Identity

Every service and worker uses:

* Workload identity
* Short-lived service credentials
* Dedicated service account
* No shared static token
* Audience-restricted authentication

## 13.3 Egress proxy

External provider traffic should pass through a controlled egress layer that records:

* Destination
* Provider
* Tool revision
* Tenant
* Request classification
* Response size
* Latency
* Cost
* Policy binding

## 13.4 Tenant isolation

Tenant identity must be attached by trusted gateway or control-plane components, never accepted solely from tool-supplied metadata.

Isolation applies to:

* Database rows
* Object-storage prefixes or buckets
* Cache keys
* Event subjects
* Vector indexes
* Logs
* Model calls
* Provider credentials
* Evaluation data

## 13.5 High-risk isolation

Tools performing:

* Code execution
* Financial commitment
* Administrative control
* Restricted-data processing

should use separate worker pools and security profiles.

---

# 14. OpenTelemetry production architecture

ServiceFabric should instrument services with OpenTelemetry SDKs and send OTLP data to regional collectors.

```text
Application SDKs
        ↓
Node-local or namespace collectors
        ↓
Regional gateway collectors
        ↓
Trace, metric, log and security backends
```

The OpenTelemetry Collector is designed as a vendor-neutral receiver, processor, and exporter, and its gateway pattern provides a shared OTLP endpoint per cluster, data center, or region.

Recommended collector responsibilities:

* Authentication
* Attribute validation
* Tenant tagging
* Redaction
* Tail sampling
* Batching
* Retry
* Backend routing
* Security-event duplication
* Cost-metric extraction

Critical audit and effect records should be written through transactional governance services, not only through best-effort telemetry.

---

# 15. Software supply-chain security

ServiceFabric should align its build pipeline with **SLSA 1.2**, the current approved SLSA specification, and produce verifiable provenance for released artifacts.

## 15.1 Required release artifacts

Every production image or bundle includes:

* Source revision
* Build identity
* Build workflow identity
* Dependency lock
* SBOM
* Test report
* Evaluation report
* Vulnerability scan
* Provenance attestation
* ToolDefinition hash
* GraphDefinition hash where relevant
* Container digest
* Signature

## 15.2 Signing

Use Sigstore Cosign for:

* Container image signatures
* Tool bundle signatures
* SBOM attestations
* Provenance attestations

Cosign supports identity-based keyless signing through OIDC and verification of signed container images and other OCI artifacts.

## 15.3 Admission policy

Production deployment should reject artifacts when:

* Signature is missing
* Signing identity is unauthorized
* Digest differs
* Provenance is missing
* SBOM is missing
* Critical vulnerabilities exceed policy
* ToolRevision hash does not match the deployment manifest
* Required evaluation report is absent

## 15.4 Dependency policy

* Lock all direct and transitive dependencies.
* Use automated update proposals.
* Prohibit floating container tags.
* Pin production images by digest.
* Remove unused dependencies.
* Maintain approved package registries.
* Verify licence policy.
* Block dependencies with known critical unresolved issues unless explicitly waived.

---

# 16. CI/CD pipeline

```text
Pull request
   ↓
Formatting and linting
   ↓
Type checking
   ↓
Unit tests
   ↓
Contract tests
   ↓
Security and secret scans
   ↓
Build artifact
   ↓
Generate SBOM
   ↓
Integration tests
   ↓
Agent-callability evaluations
   ↓
MCP conformance
   ↓
Build provenance
   ↓
Sign artifact
   ↓
Publish immutable candidate
   ↓
Deploy development
   ↓
Deploy staging
   ↓
Shadow or canary
   ↓
Production promotion
```

## 16.1 Pull-request gates

Required:

* Two-person review for control-plane or high-risk changes
* ToolDefinition diff
* Schema compatibility report
* Effect-class diff
* Policy diff
* Dependency diff
* Generated-code verification
* Test coverage for changed behaviour
* Evaluation-case updates

## 16.2 Protected changes

Require specialist review:

| Change                    | Required review         |
| ------------------------- | ----------------------- |
| Tool side-effect increase | Governance and security |
| Authorization policy      | Security                |
| Approval policy           | Governance/domain owner |
| Financial tool            | Finance control         |
| Code sandbox              | Security/platform       |
| Model data policy         | Security/data owner     |
| MCP gateway               | Platform/security       |
| Registry schema           | Platform                |
| Tool retirement           | Tool and caller owners  |

## 16.3 Promotion rules

Production promotion uses immutable artifacts.

Prohibited:

* Rebuilding during promotion
* Editing production manifests manually
* Retagging a different image as an approved version
* Changing a prompt through an unversioned configuration
* Changing provider routing without an auditable configuration version

---

# 17. Environment strategy

## 17.1 Local

Purpose:

* Capsule development
* Graph development
* Unit tests
* MCP Inspector
* Offline fixtures

Characteristics:

* Docker Compose or local Kubernetes
* stdio MCP
* Local PostgreSQL
* Local object store
* Fake policy and approval services
* No production credentials

## 17.2 Development

Purpose:

* Shared integration
* Real service boundaries
* Selected provider sandbox access

Characteristics:

* One development cluster
* Synthetic tenants
* Non-production secrets
* Aggressive telemetry
* Automatic deployment

## 17.3 Staging

Purpose:

* Production-equivalent validation
* Load tests
* Security tests
* Migration rehearsals
* Shadow and pre-canary validation

Characteristics:

* Production topology
* Restricted production-like datasets
* Provider test accounts
* Production admission policies
* Manual release gate

## 17.4 Production

Purpose:

* Supported live workloads

Characteristics:

* Immutable signed artifacts
* Real tenant isolation
* On-call ownership
* Strict audit
* Controlled canaries
* Break-glass governance

## 17.5 Evaluation

A logically separate environment or tenant for:

* Historical replay
* Model comparisons
* Adversarial testing
* Dataset fixtures
* Candidate revisions

It must be technically unable to commit ordinary production effects.

---

# 18. Repository structure

Recommended monorepo:

```text
servicefabric/
├── apps/
│   ├── mcp-gateway/
│   ├── registry-api/
│   ├── policy-service/
│   ├── approval-service/
│   ├── invocation-runtime/
│   ├── graph-runtime/
│   ├── model-gateway/
│   ├── evaluation-service/
│   ├── operations-api/
│   └── operator-console/
│
├── packages/
│   ├── contracts/
│   ├── capsule-sdk/
│   ├── graph-sdk/
│   ├── mcp-adapter/
│   ├── registry-client/
│   ├── policy-client/
│   ├── telemetry/
│   ├── error-model/
│   ├── evidence/
│   ├── test-harness/
│   └── provider-sdk/
│
├── capsules/
│   ├── math-calculate/
│   ├── research-search-papers/
│   └── ...
│
├── graphs/
│   ├── system-building/
│   ├── system-maintenance/
│   ├── system-evolution/
│   └── domain/
│
├── policies/
├── evaluations/
├── schemas/
├── infrastructure/
│   ├── kubernetes/
│   ├── helm/
│   ├── terraform/
│   └── local/
│
├── migrations/
├── runbooks/
├── architecture/
└── tools/
```

A monorepo is recommended initially because it supports:

* Atomic contract and runtime changes
* Shared SDK evolution
* Central schema validation
* Unified evaluation
* Easier dependency governance

Repository splitting should occur only when ownership, release cadence, or security isolation requires it.

---

# 19. TypeScript engineering standards

## 19.1 Compiler

Required:

```json
{
  "strict": true,
  "noUncheckedIndexedAccess": true,
  "exactOptionalPropertyTypes": true,
  "noImplicitOverride": true,
  "useUnknownInCatchVariables": true
}
```

## 19.2 Rules

* No `any` in public contracts.
* Use `unknown` for untrusted inputs.
* Validate every external boundary.
* Exhaustively match discriminated unions.
* Return typed outcomes instead of crossing service boundaries with exceptions.
* Propagate `AbortSignal`.
* Pass deadlines explicitly.
* Avoid hidden global state.
* Use dependency injection for providers, models, clocks, and identifiers.
* Use UTC internally.
* Use decimal or monetary types for financial amounts.
* Never use binary floating point for committed monetary values.

## 19.3 Package boundaries

Packages expose public entry points.

Prohibited:

```text
Deep imports into another package’s internal directory
Circular package dependencies
Runtime imports from test utilities
Tool implementation imports from MCP gateway internals
```

---

# 20. Python engineering standards

Python is appropriate for:

* Quantitative finance
* Statistical models
* Data science
* Document processing
* Evaluation workers
* Sandboxed user computation

Required:

* Supported Python version pinned by platform release
* Full type annotations on public interfaces
* Static checking
* Structured validation models
* Locked dependencies
* Reproducible environments
* No implicit notebook-only production logic
* Deterministic seeds where applicable
* Explicit numeric tolerances
* Vectorized computation only when results remain testable
* Separate model training from inference
* Exported model and data lineage

Python services must implement the same canonical ServiceFabric invocation envelope as TypeScript services.

---

# 21. Contract and API standards

## 21.1 Schemas

* JSON Schema 2020-12
* `additionalProperties: false` by default
* Stable field descriptions
* Explicit units
* Explicit time-zone semantics
* Explicit nullability
* Explicit numeric bounds
* Structured output
* Versioned error catalogue

## 21.2 Identifiers

Use time-sortable, globally unique identifiers such as UUIDv7 for operational resources.

Never expose database sequence numbers as security-sensitive public identifiers.

## 21.3 Time

* Store UTC.
* Serialize RFC 3339 timestamps.
* Include time zone for caller-facing local times.
* Distinguish observation time from retrieval time.
* Distinguish event time from processing time.

## 21.4 Pagination

Use cursor-based pagination for mutable large collections.

## 21.5 Compatibility

Every schema change receives:

* Input compatibility analysis
* Output compatibility analysis
* Error compatibility analysis
* Side-effect compatibility analysis
* Migration decision

---

# 22. Error-handling standards

Every boundary returns a stable ServiceFabric error.

Required fields:

```typescript
interface ToolError {
  code: string;
  category: string;
  retryable: boolean;
  safeMessage: string;
  details?: Record<string, unknown>;
  correlationId: string;
}
```

Rules:

* Do not expose stack traces to callers.
* Do not expose credentials or provider secrets.
* Preserve original error internally.
* Map provider errors once, at the adapter boundary.
* Do not retry validation errors.
* Do not retry authorization failures.
* Do not retry uncertain effects before reconciliation.
* Include safe repair guidance where applicable.

---

# 23. External-call standards

Every external call must declare:

* Provider
* Operation
* Timeout
* Retry policy
* Idempotency behaviour
* Maximum response size
* Data classification
* Credential binding
* Network destination
* Expected schema
* Evidence requirement

No external call may use an infinite or platform-default timeout.

Retry policy must specify:

```text
Retryable status or exception
Maximum attempts
Backoff
Jitter
Deadline interaction
Idempotency requirement
```

---

# 24. Graph engineering standards

Every graph must define:

* Input schema
* Output schema
* State schema
* Node set
* Route conditions
* Completion conditions
* Failure conditions
* Maximum depth
* Maximum node executions
* Maximum tool calls
* Maximum model calls
* Maximum cost
* Maximum duration
* Approval nodes
* Effect-verification nodes

## 24.1 Node rules

Each node must be:

* Idempotent, or explicitly non-idempotent and protected
* Independently observable
* Independently testable
* Bounded by deadline
* Bounded by resource budget
* Explicit about produced artifacts

## 24.2 Routing rules

Routing conditions should consume structured fields.

Avoid:

```text
Ask a model which arbitrary node name to execute next.
```

Prefer:

```text
Model produces structured diagnosis.
Deterministic router maps diagnosis to an allowed route.
```

## 24.3 Durable state

State transitions use optimistic concurrency:

```text
read state version N
compute transition
write state version N+1 if current version is N
```

---

# 25. Tool Capsule engineering standards

Every capsule must include:

```text
Manifest
Implementation
Maintenance graph or approved standard binding
Policy requirements
Schemas
Tests
Evaluation suite
Telemetry configuration
Documentation
Owner
Runbook
```

Required implementation properties:

* Input validation
* Output validation
* Cancellation
* Deadline
* Stable errors
* Evidence
* No undeclared dependencies
* No undeclared network access
* No undeclared model access
* No undeclared internal tools
* No manual construction of unvalidated protocol results

---

# 26. Testing standards

## 26.1 Unit tests

Cover:

* Domain logic
* Bounds
* Error mappings
* Cancellation
* Timeouts
* Deterministic helpers

## 26.2 Contract tests

Cover:

* Valid and invalid inputs
* Output schema
* Error schema
* Version compatibility
* MCP projection

## 26.3 Integration tests

Cover:

* Database
* Event bus
* Object storage
* Provider adapters
* Model gateway
* Policy service
* Approval service

## 26.4 Resilience tests

Cover:

* Provider timeout
* Duplicate event
* Worker crash
* Database failover
* Event redelivery
* Cache loss
* Telemetry loss
* Partial provider success
* Circuit breaker

## 26.5 Security tests

Cover:

* Prompt injection
* Cross-tenant access
* Token audience
* Approval forgery
* Secret exposure
* SSRF
* Sandbox escape
* Undeclared effect
* Authority expansion

## 26.6 Evaluation tests

Cover:

* Positive selection
* Negative selection
* Arguments
* Interpretation
* Recovery
* Composition
* Evidence
* Effects
* Cost

---

# 27. Database migration standards

Use expand-and-contract migrations.

```text
1. Add compatible schema.
2. Deploy code supporting old and new schema.
3. Backfill data.
4. Switch reads and writes.
5. Verify.
6. Remove old schema in a later release.
```

Rules:

* No destructive migration coupled to ordinary application startup.
* Every migration is versioned.
* Every migration has a rollback or forward-recovery plan.
* Production migrations run as dedicated Jobs.
* Large backfills are resumable.
* Migrations emit progress and audit records.
* Tool and graph state schemas retain compatibility during rolling deployments.

---

# 28. Configuration standards

Configuration should be divided into:

```text
Code:
    Behavioural implementation

Versioned configuration:
    Routing, thresholds, provider preferences

Secrets:
    Credentials and cryptographic material

Runtime state:
    Health, incidents, circuits, assignments
```

A behaviourally significant configuration change must produce:

* New configuration version
* Audit event
* Compatibility assessment
* Evaluation where relevant
* Rollback target

Prompts and model configurations are versioned behavioural artifacts.

---

# 29. Release management

## 29.1 Version layers

```text
Platform version
SDK version
Service version
ToolDefinition version
ToolRevision version
GraphDefinition version
PolicyBundle version
EvaluationSuite version
Deployment generation
```

These versions must not be conflated.

## 29.2 Release types

### Platform release

Changes shared runtimes or services.

### Tool release

Creates a new immutable ToolRevision.

### Graph release

Creates a new immutable GraphRevision.

### Policy release

Creates a new policy bundle version.

### Configuration release

Changes declared operational behaviour without rebuilding code.

## 29.3 Rollback

Rollback changes deployment routing to a prior compatible immutable artifact.

It does not mutate the failed release.

---

# 30. Service-level objectives

Initial illustrative targets:

## 30.1 MCP Gateway

```yaml
availability: 99.95%
p95ProtocolOverhead: 100ms
p99ProtocolOverhead: 250ms
```

## 30.2 Registry

```yaml
availability: 99.95%
p95DescribeTool: 100ms
p95ResolveTool: 100ms
p95CapabilitySearch: 300ms
```

## 30.3 Policy

```yaml
availability: 99.99%
p95Decision: 75ms
criticalDecisionAuditRate: 100%
```

## 30.4 Invocation runtime

```yaml
availability: 99.95%
outputValidationRate: 100%
traceLinkageRate: 99.99%
```

## 30.5 Effectful tools

```yaml
approvalBindingRate: 100%
effectVerificationRate: 100%
unauthorizedEffectRate: 0
duplicateCommittedEffectRate: 0
```

## 30.6 Durable graph runtime

```yaml
acceptedOperationDurability: 100%
lostCommittedNodeTransitions: 0
duplicateUnprotectedEffects: 0
```

SLOs should be refined after real workload baselines exist.

---

# 31. Operational ownership

Every production component requires:

* Technical owner
* Product or domain owner
* On-call group
* Escalation path
* Runbook
* SLO
* Dashboard
* Alert policy
* Backup policy
* Security classification
* Lifecycle status

## 31.1 Suggested ownership model

| Component            | Primary owner              |
| -------------------- | -------------------------- |
| MCP Gateway          | Platform engineering       |
| Capsule SDK          | Platform engineering       |
| Graph runtime        | Agent-platform engineering |
| Registry             | Platform engineering       |
| Policy and authority | Security engineering       |
| Approval service     | Governance platform        |
| Model gateway        | AI platform                |
| Evaluation service   | AI quality engineering     |
| Finance capsules     | Finance engineering/domain |
| Research capsules    | Research engineering       |
| Sandboxes            | Platform security          |
| Observability        | SRE/platform               |
| Lifecycle graphs     | Agent-platform engineering |

## 31.2 Tool ownership

Each tool has:

```text
Technical owner
Domain owner
Security reviewer class
Operational owner
Provider owner
```

No tool should enter production with only an individual developer as its undocumented owner.

---

# 32. Incident management

Incident severities:

| Severity | Example                                          |
| -------- | ------------------------------------------------ |
| SEV-1    | Unauthorized financial or administrative effect  |
| SEV-2    | Cross-tenant exposure or broad production outage |
| SEV-3    | Material quality or provider degradation         |
| SEV-4    | Localized defect with viable workaround          |

Required incident artifacts:

* Timeline
* Affected revisions
* Affected tenants
* Authority and approval records
* Effect records
* Trace references
* Immediate mitigation
* Root cause
* Corrective changes
* Regression tests
* Evolution signals

Every material incident becomes an evaluation case.

---

# 33. Phased engineering roadmap

The roadmap is governed by exit criteria rather than calendar promises.

## Phase 0 — Reference consolidation

Build on Stage 11.

Deliver:

* Convert reference workspace into the production monorepo
* Harden canonical contracts
* Add container builds
* Add local PostgreSQL and object storage
* Add OpenTelemetry instrumentation
* Add MCP Streamable HTTP gateway
* Add CI pipeline
* Sign development images

Exit criteria:

```text
math.calculate works through remote MCP.
research.search_papers works through provider fixtures.
All executions produce traces and validated envelopes.
Build artifacts have SBOM and signature.
```

## Phase 1 — Control-plane minimum viable platform

Deliver:

* Tool Registry
* Revision publication
* Deployment resolution
* Policy service
* Basic workload identity
* Operations API
* ToolStatus
* Signed resolution records

Exit criteria:

```text
Tools are published transactionally.
Callers see authorization-aware tool lists.
Each invocation resolves an immutable revision.
Quarantined revisions cannot execute.
```

## Phase 2 — Durable graph runtime

Deliver:

* GraphDefinition registry
* Persistent graph state
* Node scheduler
* Outbox/inbox processing
* Budgets
* Cancellation
* Durable operations
* Building, maintenance, and evolution graph runners

Exit criteria:

```text
Graph runs survive worker termination.
Duplicate event delivery does not duplicate protected effects.
Human-wait and approval states can resume.
```

## Phase 3 — Evaluation and lifecycle automation

Deliver:

* Evaluation suite registry
* Offline evaluation workers
* Historical replay
* Agent-callability harness
* Publication quality gates
* Maintenance health controller
* Evolution signal pipeline

Exit criteria:

```text
No revision publishes without a signed evaluation report.
Material incidents create regression cases.
ToolStatus responds to production quality signals.
```

## Phase 4 — External retrieval portfolio

Deliver:

* HTTP provider gateway
* arXiv and Crossref adapters
* Web retrieval
* FRED and SEC adapters
* Provider routing
* Circuit breakers
* Contract-drift detection

Exit criteria:

```text
External retrieval has provenance.
Provider failure produces controlled partial or fallback behaviour.
Schema drift can quarantine one provider without disabling the platform.
```

## Phase 5 — Sandboxed software and data execution

Deliver:

* Python sandbox
* Command sandbox
* Repository adapter
* Test runner
* Data transformation workers
* File and artifact controls

Exit criteria:

```text
Untrusted code has no undeclared network or filesystem access.
Sandbox escape tests pass.
Artifacts are scanned before export.
```

## Phase 6 — Governed persistent actions

Deliver:

* Approval service
* Action previews
* Effect ledger
* Idempotency
* Reconciliation
* Project task and calendar vertical slices
* Communication preparation and sending separation

Exit criteria:

```text
Every committed effect has a verified receipt.
Approval changes invalidate execution.
Timeout-after-commit cases reconcile safely.
```

## Phase 7 — Finance and licensed-data platform

Deliver:

* WRDS adapter
* CRSP and Compustat domain tools
* Financial calculation tools
* Data lineage
* Reconciliation tools
* Financial authority model
* Preparation-only transaction flow

Exit criteria:

```text
Research datasets are reproducible.
Financial calculations reconcile to reference cases.
Licensed data policy is enforced by tenant and user.
```

## Phase 8 — Production hardening

Deliver:

* Multi-zone deployment
* DR environment
* Load tests
* Security exercises
* Backup restoration tests
* On-call coverage
* SLO dashboards
* Admission policies
* Full provenance verification

Exit criteria:

```text
Production readiness review passes.
DR recovery is demonstrated.
Critical alerts route to named owners.
Supply-chain policy rejects unsigned artifacts.
```

---

# 34. Definition of done: Tool Capsule

A tool is complete only when:

```text
[ ] ToolDefinition validated
[ ] Stable owner assigned
[ ] Effect class verified
[ ] Implementation complete
[ ] Input and output schemas validated
[ ] Stable error catalogue
[ ] Timeout and cancellation implemented
[ ] Maintenance graph bound
[ ] Policy requirements defined
[ ] Approval behaviour defined
[ ] Evidence model implemented
[ ] Unit tests pass
[ ] Contract tests pass
[ ] Integration tests pass
[ ] Security tests pass
[ ] Agent-callability suite passes
[ ] MCP conformance passes
[ ] Telemetry emitted
[ ] Dashboard exists
[ ] Runbook exists
[ ] SBOM generated
[ ] Provenance generated
[ ] Artifact signed
[ ] Evaluation report signed
[ ] Canary policy defined
[ ] Rollback target defined
```

---

# 35. Definition of done: Graph

```text
[ ] Input, output, and state schemas
[ ] Every node typed
[ ] Every route deterministic or bounded
[ ] Every route terminates
[ ] Retry loops bounded
[ ] Tool access allowlisted
[ ] Model access allowlisted
[ ] Budgets enforced
[ ] State durable
[ ] Cancellation supported
[ ] Approval nodes present where required
[ ] Effects verified
[ ] Failure paths tested
[ ] Duplicate-event tests pass
[ ] Loop tests pass
[ ] Agent-callability evaluation passes
[ ] Trace topology validated
[ ] Owner and runbook assigned
```

---

# 36. Definition of done: Production service

```text
[ ] Authenticated workload identity
[ ] Authorization policy
[ ] Resource limits
[ ] Startup probe
[ ] Readiness probe
[ ] Liveness probe
[ ] Graceful shutdown
[ ] Horizontal scaling policy
[ ] Pod disruption policy
[ ] Network policy
[ ] Egress policy
[ ] Secret bindings
[ ] Database migration strategy
[ ] SLO and error budget
[ ] Dashboard
[ ] Actionable alerts
[ ] Backup or stateless recovery plan
[ ] Load test
[ ] Failure-injection test
[ ] Signed image
[ ] SBOM and provenance
[ ] On-call owner
```

---

# 37. Definition of done: Production release

```text
[ ] Immutable artifact digests
[ ] Required reviews
[ ] All blocking tests pass
[ ] Security scan passes
[ ] Compatibility report
[ ] Migration plan where needed
[ ] Evaluation report
[ ] Canary policy
[ ] Rollback plan
[ ] Documentation
[ ] Release notes
[ ] Operational owner acknowledgement
[ ] Artifact signatures verified
[ ] Deployment state recorded
```

---

# 38. Decisions deliberately deferred

## 38.1 Kubernetes operator

Begin with:

* CRD-like schemas in the registry
* Ordinary services and controllers
* Helm or equivalent deployment manifests

Build a Kubernetes operator only after:

* ToolDeployment lifecycle is stable
* Reconciliation patterns repeat
* Manual controller logic becomes costly

## 38.2 Service mesh

Begin with:

* Workload identity
* Network policy
* Application-level telemetry
* Gateway-level mTLS

Adopt a mesh only when required for:

* Uniform service-to-service encryption
* Advanced traffic policy
* Multi-cluster routing
* Operationally justified observability

## 38.3 Active-active regions

Defer until the platform has proven:

* Global effect idempotency
* Policy consistency
* Approval replication
* Cross-region reconciliation

## 38.4 Dedicated vector database

Use the primary relational platform initially. Introduce a dedicated vector system only when measured scale, recall, or isolation requirements justify it.

## 38.5 Full public marketplace

First establish:

* Trusted internal registry
* Federation review
* Ownership
* Security gates
* Compatibility management

A marketplace is an operating model, not merely a catalogue interface.

---

# 39. Production architecture invariants

```text
SF-A001  MCP remains an external protocol adapter.
SF-A002  Internal contracts do not depend on MCP transport details.
SF-A003  Published revisions are immutable.
SF-A004  Runtime status is stored separately from revisions.
SF-A005  Control-plane authority is separated from execution workers.
SF-A006  Graph state is durable.
SF-A007  Every durable transition is idempotent.
SF-A008  Event delivery is assumed to be at least once.
SF-A009  External effects are protected by idempotency and verification.
SF-A010  Every workload has a verified identity.
SF-A011  Every production artifact is signed.
SF-A012  Every production artifact has provenance and an SBOM.
SF-A013  Production images are pinned by digest.
SF-A014  High-risk effects fail closed when governance is unavailable.
SF-A015  Optional model assistance has a deterministic fallback where feasible.
SF-A016  Provider credentials never enter model context.
SF-A017  Sandbox workloads cannot access undeclared networks or files.
SF-A018  Tenant identity is attached by trusted infrastructure.
SF-A019  Redis and caches are never authoritative.
SF-A020  Critical audit evidence is not dependent solely on telemetry export.
SF-A021  Every external call has a deadline.
SF-A022  Every retry policy is bounded.
SF-A023  Every production service has an SLO and owner.
SF-A024  Every material incident becomes a regression case.
SF-A025  No tool publishes without evaluation.
SF-A026  No breaking revision promotes without migration analysis.
SF-A027  No retired revision loses its audit and evaluation history.
SF-A028  Behaviourally significant configuration is versioned.
SF-A029  Prompts and model configurations are revision artifacts.
SF-A030  Deployment promotion never rebuilds an approved artifact.
SF-A031  Production migration jobs are separate from service startup.
SF-A032  Capability discovery remains authorization-aware.
SF-A033  A tool revision remains fixed during an invocation.
SF-A034  A graph may reason broadly but act only through delegated authority.
SF-A035  Operational complexity must be justified by measured need.
```

---

# 40. Completed architectural lifecycle

The complete ServiceFabric architecture is now:

```text
Capability request
        ↓
SYSTEM-BUILDING GRAPH
        ↓
Immutable ToolRevision
        ↓
TOOL REGISTRY
        ↓
Authorization-aware discovery
        ↓
SECURITY AND GOVERNANCE
        ↓
Resolved tool invocation
        ↓
SYSTEM-MAINTENANCE GRAPH
        ↓
Verified ToolResult or effect receipt
        ↓
TELEMETRY AND EVALUATION
        ↓
Operational evidence
        ↓
SYSTEM-EVOLUTION GRAPH
        ↓
Candidate replacement revision
        ↓
Controlled evaluation and promotion
```

The production platform surrounds that lifecycle with:

```text
Kubernetes
PostgreSQL
Object storage
Durable messaging
Workload identity
Secrets management
OpenTelemetry
Signed supply-chain artifacts
CI/CD
SLOs and operational ownership
```

---

# 41. Immediate engineering backlog

The next implementation sequence should be:

```text
1. Import the Stage 11 workspace into the production monorepo.
2. Add canonical Docker images.
3. Add remote MCP Streamable HTTP transport.
4. Add PostgreSQL-backed Tool Registry.
5. Add signed revision publication.
6. Add OpenTelemetry traces across gateway and capsule runtime.
7. Add a minimal policy-decision service.
8. Add durable invocation and idempotency records.
9. Deploy math.calculate as the first production-shaped capsule.
10. Deploy research.search_papers through fixture-backed staging.
11. Add the graph-state store and worker scheduler.
12. Add publication evaluation gates.
```

The first production milestone is achieved when `math.calculate` can be:

```text
built
signed
published
discovered
authorized
resolved
invoked through remote MCP
traced
evaluated
canaried
rolled back
```

without any manual modification of its runtime artifact.
