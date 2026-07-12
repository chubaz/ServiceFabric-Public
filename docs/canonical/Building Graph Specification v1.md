# Building Graph Specification v1

**Status:** Architecture baseline
**Graph family:** `system-building`
**Default graph:** `standard-tool-building`
**API version:** `servicefabric.ai/v1alpha1`
**MCP compatibility profile:** `2025-11-25`
**Primary output:** Immutable `ToolRevision`

---

# 1. Purpose

The **System-Building Graph** transforms a capability request into a validated, evaluated, governed, and publishable ServiceFabric Tool Capsule.

```text id="6i3lcq"
Capability request
        ↓
Capability and boundary analysis
        ↓
Canonical ToolDefinition
        ↓
Implementation and graph generation
        ↓
Security and policy generation
        ↓
Testing and agent-callability evaluation
        ↓
MCP projection and conformance
        ↓
Immutable ToolRevision
        ↓
Atomic registry publication
```

The graph is responsible for constructing tools consistently. It is not merely a code generator.

It must determine:

* Whether a new tool should exist
* Whether an existing tool can satisfy the request
* Whether the capability should be a tool, resource, prompt, graph, or ordinary service
* Where the public tool boundary belongs
* What effects and risks the capability introduces
* Whether agentic backing is justified
* Which implementation adapter should be used
* Which policies, tests, evaluations, and evidence are required
* Whether the result is fit for publication

---

# 2. Normative outcome

A successful building run produces an immutable `ToolRevision` containing:

```text id="rxz3sw"
ToolRevision
├── Resolved ToolDefinition
├── Tool implementation artifact
├── Tool Capsule runtime binding
├── Maintenance graph
├── MCP projection
├── Policy bundle
├── Test suite
├── Evaluation suite
├── Test and evaluation reports
├── Documentation
├── Dependency lock
├── Software bill of materials
├── Security assessment
├── Provenance and build attestations
└── Deployment candidate
```

The graph must not publish a partially assembled tool.

Publication is an atomic transaction:

```text id="hjg8ka"
All required artifacts valid
        ↓
Registry transaction begins
        ↓
Revision, contracts and evidence written
        ↓
Registry indexes updated
        ↓
Transaction committed
        ↓
Tool becomes discoverable
```

If any required write fails, the revision remains unpublished.

---

# 3. Responsibilities

The system-building graph is responsible for five classes of work.

## 3.1 Design

* Capability decomposition
* Tool-boundary selection
* Interface design
* Error-model design
* Effect classification
* Agentic-backing determination
* Dependency design
* Maintenance responsibilities

## 3.2 Construction

* Repository scaffolding
* Implementation generation
* Adapter configuration
* Schema generation
* MCP projection generation
* Policy generation
* Documentation generation

## 3.3 Verification

* Static analysis
* Unit tests
* Contract tests
* Integration tests
* Security tests
* Failure injection
* Agent-callability evaluations
* MCP conformance tests

## 3.4 Governance

* Ownership validation
* Risk classification
* Authorization requirements
* Approval requirements
* Data-classification checks
* Human review
* Release approval

## 3.5 Publication

* Revision assembly
* Artifact signing
* Dependency locking
* Registry transaction
* Deployment-candidate creation
* Lifecycle event emission

---

# 4. Non-responsibilities

The building graph does not:

* Operate routine production calls
* Monitor ongoing provider health
* Perform ordinary runtime retries
* Change a published revision
* Automatically deploy high-risk tools into production
* Grant users access to tools
* Override security policy
* Select a tool during an ordinary external agent run
* Modify tool behaviour after publication

Those responsibilities belong to:

```text id="52k6nt"
System-Maintenance Graph
    Runtime support and health

System-Evolution Graph
    Improvement and replacement revisions

Deployment Controller
    Environment rollout

Policy Service
    Access and approval decisions

External Agent Graph
    Runtime tool selection and composition
```

---

# 5. Graph operating principle

The building graph combines deterministic nodes with bounded agentic nodes.

## 5.1 Node classes

```text id="lnx1ea"
DETERMINISTIC
    Validation, compilation, tests, policy checks

ANALYSIS_AGENT
    Requirement analysis, boundary reasoning, threat analysis

GENERATION_AGENT
    Code, schema, documentation and test generation

EVALUATION_AGENT
    Tool-selection and result-interpretation assessments

EXECUTION
    Build commands, test runners, scanners, conformance tools

HUMAN_GATE
    Risk, architectural or release approval

TRANSACTION
    Immutable artifact and registry publication
```

## 5.2 Authority hierarchy

```text id="4n0vjk"
Platform invariants
        ↓
Security and governance policy
        ↓
Canonical ToolDefinition
        ↓
Graph decisions
        ↓
Generated implementation
```

An agent node may propose changes, but it cannot override:

* Platform invariants
* Required approval
* Effect classification rules
* Data-protection policy
* Publication thresholds
* Tool-call budgets
* Required evaluation gates

## 5.3 Deterministic control plane

Graph routing must be controlled by explicit conditions.

Bad pattern:

```text id="ngad9f"
Ask an LLM whether the tool is safe, then publish it.
```

Required pattern:

```text id="0xpiuw"
Agent produces structured risk analysis
        ↓
Deterministic policy engine applies rules
        ↓
Human approval where rules require it
        ↓
Publication gate evaluates recorded evidence
```

---

# 6. Build request

A building run starts with a `ToolBuildRequest`.

```typescript id="08rt5z"
export interface ToolBuildRequest {
  buildRequestId: string;

  capability: {
    name: string;
    description: string;
    intendedUsers: string[];
    intendedCallers: string[];
    expectedOutcomes: string[];
    exampleRequests: string[];
    prohibitedOutcomes?: string[];
  };

  source?: {
    type:
      | "new_capability"
      | "existing_service"
      | "existing_graph"
      | "external_api"
      | "external_mcp"
      | "database_operation"
      | "command"
      | "human_process";

    reference?: string;
  };

  constraints?: {
    preferredDomain?: string;
    preferredToolId?: string;
    maximumLatencyMs?: number;
    maximumCostUsd?: number;
    requiredEnvironment?: string;
    dataClassification?: string;
    protocolExposure?: Array<"internal" | "mcp" | "rest">;
  };

  requester: {
    principalId: string;
    team?: string;
  };

  requestedAt: string;
}
```

## 6.1 Minimum viable request

The request must specify:

* What capability is needed
* Who or what will call it
* At least one expected outcome
* At least one representative invocation

The building graph may refine the request, but it may not invent an organizational need without evidence.

---

# 7. Build state

The graph maintains a typed `ToolBuildState`.

```typescript id="3gvrqe"
export interface ToolBuildState {
  run: {
    buildRunId: string;
    requestId: string;
    graphVersion: string;
    startedAt: string;
    currentNode: string;
    status: BuildRunStatus;
  };

  request: ToolBuildRequest;

  discovery: {
    existingCapabilities: CapabilityMatch[];
    reuseDecision?: ReuseDecision;
  };

  design: {
    capabilityModel?: CapabilityModel;
    boundaryDecision?: BoundaryDecision;
    proposedDefinition?: ToolDefinition;
    riskAssessment?: RiskAssessment;
    architectureDecision?: ToolArchitectureDecision;
  };

  implementation: {
    scaffoldRef?: string;
    sourceArtifactRef?: string;
    maintenanceGraphRef?: string;
    policyBundleRef?: string;
    mcpProjectionRef?: string;
  };

  verification: {
    staticAnalysis?: VerificationReport;
    tests?: TestReport;
    security?: SecurityReport;
    evaluations?: EvaluationReport;
    mcpConformance?: ConformanceReport;
  };

  release: {
    reviewDecisions: ReviewDecision[];
    revisionCandidate?: ToolRevisionCandidate;
    publishedRevisionId?: string;
  };

  evidence: BuildEvidenceRecord[];
  issues: BuildIssue[];
  decisions: BuildDecisionRecord[];
}
```

```typescript id="qtgg85"
export type BuildRunStatus =
  | "received"
  | "analysing"
  | "designing"
  | "constructing"
  | "verifying"
  | "awaiting_review"
  | "publishing"
  | "completed"
  | "rejected"
  | "failed"
  | "cancelled";
```

---

# 8. Graph topology

```text id="vm8i6m"
START
  ↓
B01 Intake and request validation
  ↓
B02 Capability discovery
  ↓
B03 Reuse-or-build decision
  ├── REUSE_EXISTING ───────────────→ COMPLETE_WITH_RECOMMENDATION
  ├── COMPOSE_EXISTING ─────────────→ B04
  └── BUILD_NEW ────────────────────→ B04
  ↓
B04 Capability modelling
  ↓
B05 Tool-boundary decision
  ├── NOT_A_TOOL ───────────────────→ ALTERNATIVE_ARTIFACT_PATH
  └── TOOL_CONFIRMED
  ↓
B06 Effects and risk classification
  ↓
B07 Interface design
  ↓
B08 Execution architecture
  ↓
B09 Agentic-backing design
  ↓
B10 Threat model and policy design
  ↓
B11 Definition validation gate
  ├── REPAIRABLE ───────────────────→ B04/B07/B10
  └── VALID
  ↓
B12 Capsule scaffolding
  ↓
B13 Implementation construction
  ↓
B14 Maintenance graph construction
  ↓
B15 MCP projection generation
  ↓
B16 Test and evaluation generation
  ↓
B17 Static verification
  ├── FAIL_REPAIRABLE ──────────────→ B13
  └── PASS
  ↓
B18 Unit and contract testing
  ├── FAIL_REPAIRABLE ──────────────→ B13/B16
  └── PASS
  ↓
B19 Integration and failure testing
  ├── FAIL_REPAIRABLE ──────────────→ B08/B13/B14
  └── PASS
  ↓
B20 Security verification
  ├── FAIL_REPAIRABLE ──────────────→ B10/B13
  ├── FAIL_TERMINAL ────────────────→ REJECT
  └── PASS
  ↓
B21 Agent-callability evaluation
  ├── DESCRIPTION_FAILURE ──────────→ B07
  ├── CONTRACT_FAILURE ─────────────→ B07/B13
  ├── BEHAVIOUR_FAILURE ────────────→ B13/B14
  └── PASS
  ↓
B22 MCP conformance testing
  ├── FAIL_REPAIRABLE ──────────────→ B15
  └── PASS
  ↓
B23 Documentation and operational package
  ↓
B24 Revision assembly
  ↓
B25 Review and approval gate
  ├── CHANGES_REQUESTED ────────────→ relevant prior node
  ├── REJECTED ─────────────────────→ REJECT
  └── APPROVED
  ↓
B26 Artifact signing and attestation
  ↓
B27 Atomic registry publication
  ↓
B28 Deployment-candidate creation
  ↓
COMPLETE
```

---

# 9. Stage 1 — Intake and capability discovery

## B01 — Intake and request validation

**Node type:** Deterministic

Responsibilities:

* Validate `ToolBuildRequest`
* Assign build-run identifier
* Establish trace and audit context
* Verify requester identity
* Verify requester may initiate builds
* Normalize request metadata
* Set build budgets
* Record source references

Outputs:

```typescript id="9hs80p"
interface IntakeResult {
  normalizedRequest: ToolBuildRequest;
  buildRunId: string;
  buildBudget: BuildBudget;
}
```

Possible terminal failures:

* Invalid request
* Unverified requester
* Unsupported source type
* Prohibited data classification
* Missing ownership context

---

## B02 — Capability discovery

**Node type:** Deterministic retrieval plus analysis agent

Before creating a tool, the graph searches:

* Active ServiceFabric tools
* Deprecated tools
* Internal services
* Existing graphs
* Registered external MCP capabilities
* Reusable execution adapters
* Shared maintenance graphs
* Existing policies
* Existing domain schemas

```text id="3j912k"
Requested capability
        ↓
Semantic capability search
        ↓
Contract compatibility analysis
        ↓
Operational compatibility analysis
        ↓
Candidate reuse set
```

A capability match should include:

```typescript id="sah692"
export interface CapabilityMatch {
  artifactId: string;
  artifactType: "tool" | "service" | "graph" | "external_mcp";

  semanticMatchScore: number;
  inputCompatibilityScore: number;
  outputCompatibilityScore: number;
  policyCompatibilityScore: number;

  gaps: string[];
  risks: string[];
}
```

---

## B03 — Reuse-or-build decision

**Node type:** Deterministic decision using structured analysis

Possible decisions:

```typescript id="tuio1v"
export type ReuseDecision =
  | {
      action: "reuse_existing";
      toolId: string;
      rationale: string[];
    }
  | {
      action: "compose_existing";
      toolIds: string[];
      rationale: string[];
    }
  | {
      action: "extend_existing";
      toolId: string;
      requestedChange: string;
      rationale: string[];
    }
  | {
      action: "build_new";
      rationale: string[];
    };
```

The graph should prefer reuse when an existing tool:

* Has the same semantic outcome
* Has compatible effects
* Meets data-classification requirements
* Meets latency and reliability requirements
* Is authorized for the intended callers
* Does not require misleading argument adaptation

A thin alias should not be created merely to rename an existing tool.

An extension request should normally be redirected into the system-evolution graph rather than producing a duplicate tool.

---

# 10. Stage 2 — Capability and boundary design

## B04 — Capability modelling

**Node type:** Analysis agent with structured output

The graph converts the request into a formal capability model.

```typescript id="77p3d9"
export interface CapabilityModel {
  objective: string;
  inputs: CapabilityInput[];
  outputs: CapabilityOutput[];

  preconditions: string[];
  postconditions: string[];

  successCriteria: string[];
  partialSuccessCriteria: string[];
  failureConditions: string[];

  expectedCallers: string[];
  representativeInvocations: InvocationExample[];

  prohibitedBehaviours: string[];
  assumptions: string[];
  unresolvedQuestions: string[];
}
```

A capability model must distinguish:

```text id="t9p1fw"
The user’s objective
The external tool operation
The internal implementation process
```

Example:

```text id="5g61xn"
Objective:
    Understand relevant academic literature.

Public tool operation:
    Search scholarly records.

Internal process:
    Query several providers, normalize, merge and rank records.
```

The internal process must not leak into the public interface unless callers need to control it.

---

## B05 — Tool-boundary decision

**Node type:** Analysis agent followed by deterministic validation

The graph chooses one of the following artifact types:

| Artifact       | Use when                                                        |
| -------------- | --------------------------------------------------------------- |
| Tool           | A model or graph should actively request an operation           |
| Resource       | Context should be read without representing an action           |
| Prompt         | A reusable user-initiated workflow template is needed           |
| Graph          | The capability is a multi-stage orchestration                   |
| Service        | The capability is infrastructure not directly exposed to agents |
| Composite tool | A stable bounded operation requires several internal tools      |

MCP itself distinguishes tools as model-executable functions, resources as contextual data, and prompts as reusable templates. Tool boundary criteria

A proposed tool should have:

* One clear caller-visible objective
* A bounded result
* A describable effect class
* A schema that agents can construct reliably
* A stable semantic contract
* A meaningful independent invocation
* A clear success or failure condition

### Boundary anti-patterns

Reject or decompose tools such as:

```text id="xhwyvt"
do_everything
manage_company
perform_finance
research_and_write_and_publish
fix_all_code
```

These conceal multiple effect classes and make tool selection, authorization, recovery, and evaluation unreliable.

### Composite tool rule

A composite tool is justified when:

* Callers repeatedly need the same stable sequence
* Intermediate operations are implementation details
* The sequence has one coherent success condition
* The combined side effects can be governed as one operation
* Partial completion can be represented clearly

Otherwise, composition should remain in the calling graph.

---

# 11. Stage 3 — Risk, contract and execution design

## B06 — Effects and risk classification

**Node type:** Deterministic policy analysis with agent-assisted threat enumeration

The graph determines:

```typescript id="9dqt4z"
export interface RiskAssessment {
  effectClass: EffectClass;
  destructive: boolean;
  reversible: boolean;
  idempotencyClass: string;
  openWorld: boolean;

  dataClasses: string[];
  externalDestinations: string[];

  codeExecution: boolean;
  financialEffect: boolean;
  externalCommunication: boolean;
  administrativeControl: boolean;

  riskLevel: "low" | "medium" | "high" | "critical";
  approvalMode: "none" | "policy" | "always";

  threatScenarios: ThreatScenario[];
  requiredControls: string[];
}
```

Risk classification must be based on actual implementation effects rather than tool naming.

Example:

```text id="o826pi"
Tool name: finance.prepare_payment
Declared effect: pure transformation
Actual implementation: submits payment to bank

Result: reject definition because declared and actual effects conflict.
```

---

## B07 — Interface design

**Node type:** Generation agent plus deterministic schema validation

This node generates:

* Tool identifier
* Title
* Concise description
* `whenToUse`
* `whenNotToUse`
* Input schema
* Output schema
* Error catalogue
* Invocation examples
* Result examples

### Interface-design order

```text id="0u6fs4"
Success semantics
        ↓
Output data model
        ↓
Error and partial-result semantics
        ↓
Input requirements
        ↓
Agent-facing description
```

Starting with provider parameters often produces a provider-shaped tool rather than a user-shaped tool.

### Schema requirements

* Inputs are object-shaped.
* Required arguments are minimized.
* Defaults are safe.
* Fields use domain language.
* Implementation controls remain hidden.
* Unknown properties are rejected by default.
* Every field has a useful description.
* Output is structured.
* Errors are stable and actionable.

The released MCP specification supports optional output schemas; when one is declared, servers must return conforming structured results and clients should validate them. It also distinguishes protocol errors from repairable tool-execution errors. Compatibility profile

The building graph should compile schemas against two profiles:

```text id="ynh6hm"
SERVICEFABRIC_CANONICAL
    Full internal schema and validation

MCP_2025_11_25
    Projection compatible with released MCP
```

Protocol projection must be replaceable so future MCP schema evolution does not require changing internal domain contracts.

---

## B08 — Execution architecture

**Node type:** Analysis agent plus deterministic adapter selection

The graph selects:

```typescript id="2n4kwe"
export interface ToolArchitectureDecision {
  adapter:
    | "native_function"
    | "native_service"
    | "internal_graph"
    | "external_http"
    | "database_operation"
    | "command_runner"
    | "federated_mcp"
    | "human_task";

  deploymentMode:
    | "shared_runtime"
    | "dedicated_service"
    | "graph_runtime"
    | "federated";

  targetReference: string;

  rationale: string[];
  rejectedAlternatives: ArchitectureAlternative[];

  scalingModel: string;
  stateModel: string;
  timeoutModel: string;
}
```

### Adapter-selection rules

Use `native_function` when:

* Execution is deterministic
* Dependencies are small
* No external network is needed
* Isolation requirements are limited

Use `native_service` when:

* Independent scaling is needed
* Specialized dependencies are required
* The capability already exists as a service
* Fault isolation is important

Use `internal_graph` when:

* Several decisions or tool calls are required
* Execution is genuinely multi-step
* Intermediate state matters
* Recovery cannot be represented as a simple adapter retry

Use `federated_mcp` when:

* A third-party MCP server already provides the capability
* ServiceFabric policy and normalization must surround it
* Tool-list or contract drift can be monitored

Use `command_runner` only within a sandbox.

---

## B09 — Agentic-backing design

**Node type:** Analysis agent followed by budget and policy validation

The graph must first ask:

```text id="j1amtr"
Can this capability be implemented correctly without a model?
```

If yes, model use should generally be omitted.

### Model-use justification

```typescript id="08t79t"
export interface AgenticBackingDecision {
  level:
    | "none"
    | "guarded"
    | "assisted"
    | "agentic"
    | "autonomous";

  modelNecessary: boolean;
  justification?: string;

  modelPurposes: string[];
  prohibitedModelPurposes: string[];

  internalTools: string[];
  completionCriteria: string[];

  budgets: {
    maximumInternalToolCalls: number;
    maximumModelCalls: number;
    maximumTokens: number;
    maximumCostUsd: number;
    maximumDepth: number;
  };
}
```

### Appropriate model responsibilities

* Query reformulation
* Semantic classification
* Relevance ranking
* Ambiguity identification
* Structured extraction from unstructured text
* Planning within a bounded operation
* Explanation generation

### Inappropriate sole model responsibilities

* Authorization
* Approval validation
* Financial-limit enforcement
* Exact arithmetic
* Secret selection
* Effect confirmation
* Schema validation
* Provider identity validation
* Publication decision

---

## B10 — Threat model and policy design

**Node type:** Security-analysis agent plus deterministic policy compiler

The graph evaluates:

* Authentication
* Authorization
* Tenant isolation
* Data leakage
* Prompt injection
* Secret handling
* Provider trust
* SSRF
* Command execution
* Dependency compromise
* Token passthrough
* Replay and idempotency
* Excessive tool recursion
* Cost amplification
* Incorrect effect declaration
* Output poisoning
* Evidence fabrication

Generated policies include:

```text id="8185b7"
Authorization policy
Approval policy
Data-classification policy
Network-egress policy
Secret-binding policy
Model-use policy
Internal-tool allowlist
Retention policy
Logging-redaction policy
Effect-verification policy
```

The stable MCP tools specification requires servers to validate inputs, implement access controls, rate-limit invocations, and sanitize outputs. ServiceFabric’s generated policy bundle treats those as minimum controls rather than the complete security model.

## B11 — Definition validation gate

**Node type:** Deterministic

This gate validates the proposed `ToolDefinition`.

Checks include:

```text id="k4v56u"
Manifest schema
Identifier uniqueness
Owner assignment
Interface consistency
Effect consistency
Authorization completeness
Approval completeness
Agentic budget completeness
Dependency resolvability
Maintenance graph responsibilities
MCP projection feasibility
Evaluation requirements
```

Possible outcomes:

```typescript id="8cjdt4"
type DefinitionGateDecision =
  | { outcome: "pass" }
  | {
      outcome: "repair";
      targetNodes: string[];
      issues: BuildIssue[];
    }
  | {
      outcome: "reject";
      issues: BuildIssue[];
    };
```

Terminal rejection examples:

* Prohibited effect
* No legitimate owner
* Inherently misleading capability
* Required security control unavailable
* Undeclarable or unverifiable effect
* Source dependency cannot legally or technically be used
* Tool boundary remains unbounded after repair attempts

---

# 12. Stage 4 — Construction

## B12 — Capsule scaffolding

**Node type:** Deterministic generator

The node creates:

```text id="gpy5mk"
capsules/<tool-id>/
├── manifest/tool.yaml
├── src/
├── maintenance/
├── policies/
├── tests/
├── evaluations/
├── docs/
└── package configuration
```

Scaffolding is generated from templates versioned independently of individual tools.

```typescript id="5vymrv"
export interface ScaffoldMetadata {
  templateId: string;
  templateVersion: string;
  generatedAt: string;
  sourceDefinitionHash: string;
}
```

Generated files must identify:

* Generated sections
* Human-maintained sections
* Regeneration behaviour
* Source template
* Definition hash

---

## B13 — Implementation construction

**Node type:** Generation agent and execution environment

Implementation construction may:

* Generate new code
* Bind an existing service
* Generate an API mapper
* Generate a database operation
* Generate a federated MCP adapter
* Bind an internal graph
* Produce a human-task workflow

### Code-generation inputs

The generation node receives only:

* Resolved `ToolDefinition`
* Approved architecture decision
* Approved dependencies
* Capsule SDK documentation
* Relevant domain contracts
* Generated policy interfaces
* Test requirements

It should not receive unrestricted repository access.

### Generation restrictions

Generated code may not:

* Add undeclared dependencies
* Add undeclared network destinations
* Read unrestricted environment variables
* Invoke undeclared tools
* Invoke undeclared models
* Change the effect class
* Suppress telemetry
* Construct its own authorization bypass
* Return data outside the output contract

### Implementation completion criteria

* Code compiles
* Every tool contract method is implemented
* Cancellation is propagated
* Deadline is respected
* Provider errors are mapped
* Evidence is returned where required
* No public result envelope is manually constructed
* No policy decision is embedded as mutable business logic

---

## B14 — Maintenance graph construction

**Node type:** Graph generator plus deterministic graph validation

The building graph generates or binds a maintenance graph.

```text id="ebixq0"
Maintenance graph
├── beforeCall
├── afterExecution
├── afterCall
└── onFailure
```

The graph must implement declared responsibilities such as:

* Domain precondition checks
* Provider routing
* Retry
* Fallback
* Output normalization
* Evidence validation
* Partial-result classification
* Status updates

### Reuse rule

A standard maintenance graph should be reused for simple classes:

```text id="v4ztex"
deterministic-tool-maintenance
external-read-maintenance
reversible-write-maintenance
command-execution-maintenance
federated-mcp-maintenance
```

A bespoke maintenance graph is justified only when domain-specific execution support is necessary.

### Graph validation

The maintenance graph compiler checks:

* All referenced nodes exist.
* Every execution path terminates.
* Retry loops are bounded.
* Fallback loops are bounded.
* Tool and model access matches allowlists.
* Budgets are enforced.
* Policy gates cannot be bypassed.
* Failure outcomes map to stable errors.
* Quarantine routes are reachable.
* Output validation occurs before return.

---

## B15 — MCP projection generation

**Node type:** Deterministic compiler

The MCP projection is generated from the canonical manifest.

```text id="y0f6ux"
ToolDefinition
    ↓
Compatibility-profile compiler
    ↓
MCP descriptor
    ↓
MCP registration artifact
    ↓
Conformance fixtures
```

Generated fields include:

* Tool name
* Title
* Agent-facing description
* Input schema
* Output schema
* Annotations
* Execution metadata
* Safe `_meta` fields

The official TypeScript SDK’s server architecture registers tools on an `McpServer` and connects that server through Streamable HTTP for remote deployment or stdio for local integrations. ServiceFabric should isolate those SDK-specific calls inside its MCP adapter package.

## B16 — Test and evaluation generation

**Node type:** Generation agent plus deterministic coverage checker

The graph generates:

```text id="9by6p2"
Unit tests
Contract tests
Integration tests
Maintenance tests
Security tests
Failure-injection tests
Agent-callability tests
MCP conformance tests
Performance tests
```

### Test-source diversity

Tests should come from:

* Capability examples
* Schema boundaries
* Threat scenarios
* Provider documentation
* Historical failures from similar tools
* Platform invariants
* Adversarial generation
* Human-authored critical cases

The same model output should not be used as both implementation and sole evaluator.

---

# 13. Stage 5 — Verification

## B17 — Static verification

**Node type:** Deterministic execution

Checks:

* Type checking
* Compilation
* Linting
* Dependency allowlist
* Secret scanning
* License policy
* Vulnerability scanning
* Forbidden API usage
* Network-destination extraction
* Tool-call extraction
* Model-call extraction
* Dead-code and unreachable-route checks
* Manifest-to-code consistency

Example consistency rules:

```text id="byvg9j"
Code performs HTTP request
    → destination must appear in network policy

Code calls another tool
    → tool must appear in internalToolAccess

Code calls a model
    → modelUse.permitted must be true

Code writes persistent state
    → effects.persistentMutation must be true

Code launches a process
    → adapter must permit command execution
```

---

## B18 — Unit and contract testing

**Node type:** Deterministic execution

Required tests:

* Valid input
* Every required field
* Boundary values
* Unknown fields
* Invalid formats
* Expected output
* Partial output
* Every stable error category
* Cancellation
* Timeout
* Result-envelope construction
* Output-schema validation

Minimum publication threshold:

```text id="vkbff8"
Contract tests: 100% pass
Schema-valid output: 100%
Platform invariants: 100%
```

Coverage percentage alone must not determine readiness.

---

## B19 — Integration and failure testing

**Node type:** Execution and fault-injection nodes

Failure scenarios include:

* Provider unavailable
* Slow provider
* Rate limit
* Invalid provider response
* Schema drift
* Empty response
* Duplicate response
* Stale result
* Authentication expiry
* Network interruption
* Partial provider success
* Cache corruption
* Cancellation during execution
* Dependency circuit open
* Internal tool failure
* Model malformed output
* Budget exhaustion

The graph verifies that the capsule:

* Returns a stable error
* Retries only permitted failures
* Uses only declared fallbacks
* Respects deadlines
* Preserves idempotency
* Does not leak provider internals
* Records correct telemetry
* Does not claim success without evidence

---

## B20 — Security verification

**Node type:** Deterministic scanner, adversarial agent, and policy evaluator

Security tests include:

```text id="xblp4g"
Unauthorized caller
Missing scope
Expired approval
Approval for altered arguments
Cross-tenant request
Prompt injection in external content
Secret-extraction request
Token-passthrough attempt
SSRF destination
Oversized response
Recursive tool-call attempt
Budget-amplification attempt
Malicious provider metadata
Forged effect receipt
Replay of state-changing invocation
```

### Security outcomes

```typescript id="npgoce"
export type SecurityOutcome =
  | "pass"
  | "repair_required"
  | "manual_security_review"
  | "terminal_rejection";
```

High- and critical-risk tools require human security review even when automated tests pass.

---

## B21 — Agent-callability evaluation

**Node type:** Evaluation harness using multiple caller profiles

This stage tests the tool as an agent-facing capability rather than only as software.

## 13.1 Selection evaluation

The evaluator gives agents a mixed tool catalogue and measures whether they:

* Select the tool for valid use cases
* Avoid it for invalid use cases
* Prefer a more appropriate existing tool
* Avoid unnecessary calls
* Recognize approval requirements
* Recognize tool limitations

Metrics:

```text id="0g9lkx"
Selection precision
Selection recall
Unnecessary-call rate
Unsafe-selection rate
Tool-confusion matrix
```

## 13.2 Argument-construction evaluation

The evaluator measures:

* Schema-valid call rate
* Correct field use
* Default use
* Constraint compliance
* Date and identifier formatting
* Recovery after validation feedback

## 13.3 Result-interpretation evaluation

The evaluator measures whether callers:

* Distinguish success from partial success
* Interpret warnings
* Use evidence correctly
* Avoid treating missing data as fact
* Respond properly to retryable errors
* Avoid retrying terminal errors
* Respect effect receipts

## 13.4 Composition evaluation

The evaluator tests whether the tool composes appropriately with:

* Search tools
* Retrieval tools
* Calculators
* File tools
* Code tools
* Task systems
* Reporting tools

## 13.5 Description repair loop

Failures are classified:

```text id="hiskf8"
Selection failure
    → improve purpose, whenToUse or whenNotToUse

Argument failure
    → simplify schema or improve field descriptions

Interpretation failure
    → improve output structure, warnings or examples

Behaviour failure
    → modify implementation or maintenance graph

Composition failure
    → reconsider tool boundary
```

---

## B22 — MCP conformance testing

**Node type:** Deterministic protocol harness

The test server verifies:

* Initialization
* Protocol-version handling
* Capability negotiation
* Tool listing
* Pagination where used
* Tool invocation
* Input rejection
* Structured output
* Tool-execution errors
* Protocol errors
* Cancellation
* Progress where declared
* List-change handling where declared
* Remote transport
* Local stdio transport

The released MCP specification uses JSON-RPC, capability negotiation, and model-executable tools; the building graph pins conformance to an explicit released profile rather than testing against an unversioned moving target.

# 14. Stage 6 — Documentation and release assembly

## B23 — Documentation and operational package

**Node type:** Generation agent plus factual consistency validator

Required documentation:

```text id="lj5f3f"
README
Purpose and limitations
Input and output contract
Examples
Error catalogue
Permissions
Side effects
Approval requirements
Operational dependencies
Maintenance behaviour
Provider behaviour
Troubleshooting
Deprecation policy
```

Documentation must be generated from canonical artifacts where possible.

The consistency checker rejects contradictions such as:

```text id="1ogroq"
Documentation says read-only
Manifest says write-reversible

Documentation says no model
Implementation invokes model client

Documentation says no approval
Policy requires approval
```

---

## B24 — Revision assembly

**Node type:** Deterministic

The graph assembles a `ToolRevisionCandidate`.

```typescript id="hmk2u3"
export interface ToolRevisionCandidate {
  toolId: string;
  version: string;
  revisionId: string;

  definitionRef: string;
  implementationArtifactRef: string;
  maintenanceGraphRef: string;
  mcpProjectionRef: string;
  policyBundleRef: string;
  testSuiteRef: string;
  evaluationSuiteRef: string;
  documentationRef: string;

  dependencyLockRef: string;
  softwareBillOfMaterialsRef: string;

  reports: {
    staticAnalysis: string;
    tests: string;
    security: string;
    evaluations: string;
    mcpConformance: string;
  };

  contentHash: string;
}
```

The revision hash covers all behaviourally relevant artifacts.

A changed implementation, policy, schema, graph, dependency lock, or prompt must produce a different hash.

---

# 15. Review and approval

## B25 — Review and approval gate

**Node type:** Deterministic reviewer assignment plus human gates

Required reviews depend on risk.

| Risk     | Required review                                         |
| -------- | ------------------------------------------------------- |
| Low      | Automated gates and owner approval                      |
| Medium   | Technical owner and domain owner                        |
| High     | Technical, domain, security and governance              |
| Critical | Security, governance and designated executive authority |

Additional mandatory review triggers:

* Financial effect
* Irreversible write
* External communication
* Arbitrary code execution
* Confidential or restricted data
* Autonomous agentic backing
* New third-party provider
* New external MCP server
* New administrative control

## 15.1 Review package

Reviewers receive:

* Capability summary
* Tool contract
* Boundary rationale
* Rejected alternatives
* Effects
* Threat model
* Policies
* Agentic-backing justification
* Test results
* Evaluation results
* Known limitations
* Deployment recommendation

## 15.2 Review decisions

```typescript id="my10v8"
export interface ReviewDecision {
  reviewer: string;
  role: string;

  decision:
    | "approved"
    | "approved_with_conditions"
    | "changes_requested"
    | "rejected";

  comments?: string;
  conditions?: string[];

  artifactHash: string;
  decidedAt: string;
}
```

Approval is bound to the artifact hash. Changes after approval invalidate affected approvals.

---

# 16. Signing, attestation and publication

## B26 — Artifact signing and attestation

**Node type:** Deterministic supply-chain service

Attestations include:

* Source request
* ToolDefinition hash
* Source-code commit
* Build template version
* Graph version
* Build environment
* Dependency lock
* Test reports
* Evaluation reports
* Review decisions
* Final content hash

The graph records which artifacts were:

* Human-authored
* Agent-generated
* Deterministically generated
* Imported from an existing service
* Retrieved from a provider

---

## B27 — Atomic registry publication

**Node type:** Transaction

```typescript id="r9pluj"
export interface PublishToolRevisionTransaction {
  begin(): Promise<string>;

  writeRevision(
    transactionId: string,
    revision: SignedToolRevision
  ): Promise<void>;

  writeIndexes(
    transactionId: string,
    indexes: ToolRegistryIndexes
  ): Promise<void>;

  verify(
    transactionId: string
  ): Promise<PublicationVerification>;

  commit(transactionId: string): Promise<void>;
  rollback(transactionId: string): Promise<void>;
}
```

Publication conditions:

```text id="4atfbg"
All mandatory reports pass
Required approvals match artifact hash
Content hash is valid
Version is available
Dependencies are resolvable
Maintenance graph is published
Policy bundle is published
MCP projection passes conformance
Deployment artifact is retrievable
```

After commit, the revision is immutable.

---

## B28 — Deployment-candidate creation

**Node type:** Deterministic

The building graph creates, but does not necessarily activate, a deployment candidate.

```typescript id="z79ii9"
export interface ToolDeploymentCandidate {
  toolRevisionId: string;
  targetEnvironment: string;

  rollout:
    strategy: "manual" | "canary" | "blue_green";
    initialTrafficPercentage: number;

  requiredChecks: string[];
  rollbackRevisionId?: string;
}
```

Default recommendations:

```text id="ctvc78"
Low-risk deterministic tool:
    automated canary permitted

External-data tool:
    canary with provider monitoring

State-changing tool:
    manual activation

Financial or administrative tool:
    separate deployment approval
```

---

# 17. Repair loops

A building graph must support repair without becoming unbounded.

## 17.1 Repair budget

```typescript id="6j8cvt"
export interface BuildRepairBudget {
  maximumTotalRepairCycles: number;
  maximumCyclesPerStage: number;
  maximumGenerationCalls: number;
  maximumEvaluationCalls: number;
  maximumBuildCostUsd: number;
}
```

Suggested default:

```yaml id="0znw6p"
maximumTotalRepairCycles: 12
maximumCyclesPerStage: 3
maximumGenerationCalls: 20
maximumEvaluationCalls: 12
maximumBuildCostUsd: 10
```

Actual limits should depend on tool complexity.

## 17.2 Repair routing

Every failed gate returns:

* Stable issue code
* Severity
* Affected artifact
* Responsible prior node
* Suggested repair class
* Whether human intervention is required

```typescript id="aq6urm"
export interface BuildIssue {
  code: string;
  severity: "info" | "warning" | "error" | "critical";
  category: string;

  artifactRef?: string;
  message: string;

  repairable: boolean;
  repairNode?: string;
  humanReviewRequired: boolean;
}
```

## 17.3 Termination conditions

The graph terminates unsuccessfully when:

* Repair budget is exhausted.
* The same critical failure recurs three times.
* Required policy cannot be satisfied.
* Tool boundary remains incoherent.
* A reviewer rejects the capability.
* Source dependency is prohibited.
* Required evidence cannot be produced.
* Generated behaviour cannot be reconciled with declared effects.

---

# 18. Build evidence and decision records

Every significant design choice must be auditable.

```typescript id="gnll46"
export interface BuildDecisionRecord {
  decisionId: string;
  stage: string;

  question: string;
  selectedOption: string;
  alternatives: string[];

  rationale: string[];
  evidenceRefs: string[];

  decisionMaker:
    | "deterministic_rule"
    | "analysis_agent"
    | "human_reviewer";

  modelExecutionRef?: string;
  createdAt: string;
}
```

Important decision records include:

* Reuse versus build
* Tool versus graph
* Public tool boundary
* Effect class
* Adapter
* Agentic-backing level
* Provider selection strategy
* Approval policy
* Schema shape
* Maintenance-graph reuse
* Publication recommendation

The graph should record conclusions and evidence, not private model reasoning.

---

# 19. Graph node interface

```typescript id="v4otj6"
export interface BuildGraphNode<
  TInput = ToolBuildState,
  TOutput = Partial<ToolBuildState>
> {
  id: string;
  version: string;
  type:
    | "deterministic"
    | "analysis_agent"
    | "generation_agent"
    | "evaluation_agent"
    | "execution"
    | "human_gate"
    | "transaction";

  execute(
    input: TInput,
    context: BuildNodeContext
  ): Promise<BuildNodeResult<TOutput>>;
}
```

```typescript id="47e3no"
export interface BuildNodeContext {
  runId: string;
  signal: AbortSignal;
  deadline: Date;

  artifacts: BuildArtifactStore;
  registry: ToolRegistryClient;
  policies: BuildPolicyClient;

  tools: RestrictedBuildToolClient;
  models: RestrictedBuildModelClient;
  humanReview: ReviewService;

  trace: TraceContext;
  audit: AuditRecorder;
  budget: BuildBudgetController;
}
```

```typescript id="9og6bb"
export type BuildNodeResult<T> =
  | {
      outcome: "completed";
      statePatch: T;
      nextNode?: string;
      evidence: BuildEvidenceRecord[];
    }
  | {
      outcome: "repair_required";
      issues: BuildIssue[];
      nextNode: string;
    }
  | {
      outcome: "human_review_required";
      reviewRequest: ReviewRequest;
    }
  | {
      outcome: "rejected";
      issues: BuildIssue[];
    }
  | {
      outcome: "failed";
      error: BuildGraphError;
    };
```

---

# 20. Declarative graph definition

```yaml id="budp8u"
apiVersion: servicefabric.ai/v1alpha1
kind: SystemBuildingGraph

metadata:
  id: standard-tool-building
  version: 1.0.0
  owner: servicefabric-platform

spec:
  entryNode: intake

  budgets:
    maximumDuration: PT4H
    maximumRepairCycles: 12
    maximumModelCalls: 40
    maximumCostUsd: 25

  nodes:
    intake:
      type: deterministic
      handler: build.intake
      next: capability-discovery

    capability-discovery:
      type: analysis_agent
      handler: build.discover-capabilities
      tools:
        - registry.search_capabilities
        - registry.read_contract
      outputSchemaRef: schemas/capability-discovery.json
      next: reuse-decision

    reuse-decision:
      type: deterministic
      handler: build.decide-reuse
      routes:
        reuse_existing: complete-recommendation
        compose_existing: capability-model
        extend_existing: redirect-evolution
        build_new: capability-model

    capability-model:
      type: analysis_agent
      handler: build.model-capability
      outputSchemaRef: schemas/capability-model.json
      next: boundary-decision

    boundary-decision:
      type: analysis_agent
      handler: build.select-boundary
      routes:
        tool: risk-classification
        composite_tool: risk-classification
        graph: build-graph-artifact
        resource: build-resource-artifact
        prompt: build-prompt-artifact
        service: build-service-artifact
        reject: reject

    risk-classification:
      type: deterministic
      handler: build.classify-risk
      next: interface-design

    interface-design:
      type: generation_agent
      handler: build.design-interface
      next: architecture-design

    architecture-design:
      type: analysis_agent
      handler: build.select-architecture
      next: agentic-backing-design

    agentic-backing-design:
      type: analysis_agent
      handler: build.design-agentic-backing
      next: threat-and-policy-design

    threat-and-policy-design:
      type: analysis_agent
      handler: build.design-security
      next: definition-gate

    definition-gate:
      type: deterministic
      handler: build.validate-definition
      routes:
        pass: scaffold
        repair_capability: capability-model
        repair_interface: interface-design
        repair_security: threat-and-policy-design
        reject: reject

    scaffold:
      type: deterministic
      handler: build.generate-scaffold
      next: implementation

    implementation:
      type: generation_agent
      handler: build.construct-implementation
      next: maintenance-graph

    maintenance-graph:
      type: generation_agent
      handler: build.construct-maintenance-graph
      next: mcp-projection

    mcp-projection:
      type: deterministic
      handler: build.generate-mcp-projection
      next: test-generation

    test-generation:
      type: generation_agent
      handler: build.generate-tests
      next: static-verification

    static-verification:
      type: execution
      handler: build.run-static-verification
      routes:
        pass: contract-tests
        repair: implementation
        reject: reject

    contract-tests:
      type: execution
      handler: build.run-contract-tests
      routes:
        pass: integration-tests
        repair_implementation: implementation
        repair_tests: test-generation

    integration-tests:
      type: execution
      handler: build.run-integration-tests
      routes:
        pass: security-verification
        repair_architecture: architecture-design
        repair_implementation: implementation
        repair_maintenance: maintenance-graph

    security-verification:
      type: evaluation_agent
      handler: build.run-security-evaluation
      routes:
        pass: agent-evaluation
        repair: threat-and-policy-design
        human_review: security-review
        reject: reject

    agent-evaluation:
      type: evaluation_agent
      handler: build.run-agent-callability-evaluation
      routes:
        pass: mcp-conformance
        repair_description: interface-design
        repair_contract: interface-design
        repair_behaviour: implementation
        reconsider_boundary: boundary-decision

    mcp-conformance:
      type: execution
      handler: build.run-mcp-conformance
      routes:
        pass: documentation
        repair: mcp-projection

    documentation:
      type: generation_agent
      handler: build.generate-documentation
      next: assemble-revision

    assemble-revision:
      type: deterministic
      handler: build.assemble-revision
      next: release-review

    release-review:
      type: human_gate
      handler: build.review-release
      routes:
        approved: sign-artifacts
        changes_requested: route-requested-changes
        rejected: reject

    sign-artifacts:
      type: transaction
      handler: build.sign-and-attest
      next: publish

    publish:
      type: transaction
      handler: build.publish-revision
      next: deployment-candidate

    deployment-candidate:
      type: deterministic
      handler: build.create-deployment-candidate
      next: complete
```

---

# 21. Specialized building-graph profiles

The standard graph should support profiles rather than forcing every tool through unnecessary stages.

## 21.1 Deterministic primitive profile

For:

* Calculator
* Parser
* Formatter
* Unit converter

Differences:

* No model-use design beyond confirming prohibition
* Standard deterministic maintenance graph
* No provider routing
* Lightweight integration testing
* Strong property-based testing

## 21.2 External retrieval profile

For:

* Web search
* Weather
* Scholarly search
* Market-data retrieval

Additional stages:

* Provider-contract analysis
* Freshness semantics
* Source-provenance tests
* Rate-limit tests
* Provider-drift tests
* Partial-result tests

## 21.3 State-changing profile

For:

* Create task
* Send email
* Update calendar
* Modify repository

Additional stages:

* Action-preview design
* Approval workflow
* Idempotency design
* Effect-receipt schema
* Rollback or compensation design
* Replay tests

## 21.4 Code-execution profile

For:

* Test runner
* Compiler
* Data script
* Static analyzer

Additional stages:

* Sandbox design
* Resource-limit tests
* Filesystem policy
* Process policy
* Network-isolation tests
* Malicious-input tests

## 21.5 Federated MCP profile

For third-party MCP servers:

* Server identity verification
* Tool inventory import
* Contract normalization
* Tool-by-tool risk classification
* Authentication isolation
* Tool-list drift monitoring
* Output sanitation
* Provider quarantine policy

## 21.6 Agent-backed profile

For:

* Research investigation
* Software failure analysis
* Financial report analysis
* Organisational diagnostic

Additional stages:

* Internal graph design
* Model-purpose validation
* Internal-tool allowlist
* Recursion tests
* Evidence sufficiency tests
* Model and provider substitution tests
* Completion and stopping-condition tests

---

# 22. Reference build: `math.calculate`

```text id="hyk709"
Request:
    Provide exact bounded mathematical evaluation.

Discovery:
    No compatible active tool.

Boundary:
    One deterministic tool.

Effects:
    Pure, read-only, closed-world.

Interface:
    expression → result and normalized expression.

Architecture:
    Native function in shared runtime.

Agentic backing:
    Guarded; no model use.

Policies:
    Standard calculator authorization.
    No network.
    No filesystem.
    Expression complexity limit.

Implementation:
    Safe parser and evaluator.
    No eval() or arbitrary code execution.

Tests:
    Arithmetic
    Precedence
    Bounds
    Invalid expressions
    Resource-exhaustion expressions
    Property-based cases

Agent evaluation:
    Select calculator for exact arithmetic.
    Avoid calculator for market-data retrieval.

MCP projection:
    math.calculate

Publication:
    Low-risk automated canary eligible.
```

---

# 23. Reference build: `research.search_papers`

```text id="k13lw4"
Request:
    Discover scholarly papers relevant to a research question.

Discovery:
    Provider-specific services exist but no normalized public tool.

Boundary:
    One retrieval tool.
    Full-paper retrieval remains separate.

Effects:
    Read external, open-world, medium risk.

Interface:
    Research query, date bounds, result limit.
    Structured records with identifiers and provenance.

Architecture:
    Native research service with external providers.

Agentic backing:
    Assisted.
    Model permitted for query reformulation and ranking.
    Model prohibited from creating citations.

Policies:
    External destination allowlist.
    Provider credentials hidden.
    Public/internal input classification.
    Provenance required.

Maintenance graph:
    Provider selection
    Query normalization
    Retry
    Fallback
    Merge
    Deduplication
    Identifier validation
    Partial-result classification

Tests:
    Provider timeouts
    Duplicate records
    Invalid DOI
    Empty result
    Conflicting metadata
    Prompt injection in abstracts

Agent evaluation:
    Use for scholarly discovery.
    Do not use for known-document full-text retrieval.
    Do not treat returned abstracts as verified quotations.

Publication:
    Medium-risk owner and domain review.
```

---

# 24. System-building graph invariants

```text id="dn1b3g"
SF-B001  Every build starts from a verified request.
SF-B002  Every build searches for reusable capabilities first.
SF-B003  Every proposed tool receives an explicit boundary decision.
SF-B004  Every tool has one bounded caller-visible objective.
SF-B005  Every tool has an explicit effect classification.
SF-B006  Every risk decision produces structured evidence.
SF-B007  Every model use has a declared purpose and budget.
SF-B008  No model makes the final authorization decision.
SF-B009  Generated code cannot add undeclared dependencies.
SF-B010  Generated code cannot add undeclared network access.
SF-B011  Every tool receives a maintenance graph.
SF-B012  Every MCP projection is generated from the canonical definition.
SF-B013  Every native tool defines structured output.
SF-B014  Every tool-level error has a stable error code.
SF-B015  Every external-data tool has provenance tests.
SF-B016  Every state-changing tool has idempotency policy.
SF-B017  Every state-changing tool has effect verification.
SF-B018  Every high-risk tool receives human security review.
SF-B019  Every tool passes agent-callability evaluation.
SF-B020  Every MCP-exposed tool passes a pinned conformance profile.
SF-B021  Every repair loop is bounded.
SF-B022  Every revision hash covers behaviourally relevant artifacts.
SF-B023  Every approval is bound to an artifact hash.
SF-B024  Every published revision is immutable.
SF-B025  Publication is atomic.
SF-B026  A failed build cannot become discoverable.
SF-B027  Build decisions retain evidence and alternatives.
SF-B028  Agent-generated artifacts are identified as such.
SF-B029  Tool construction and deployment approval remain separable.
SF-B030  An existing tool extension is routed to the evolution graph.
```

---

# 25. Final architectural decision

The ServiceFabric system-building process should operate as a compiler with agent-assisted design stages.

```text id="x5l63r"
Capability intent
      ↓
Semantic analysis
      ↓
Canonical intermediate representation:
ToolDefinition
      ↓
Code, graph, policy and MCP generation
      ↓
Static and dynamic verification
      ↓
Agent-callability evaluation
      ↓
Immutable executable revision
```

The `ToolDefinition` is analogous to an intermediate representation:

* The capability request is the source language.
* Analysis agents help construct the representation.
* Deterministic compilers generate protocol and runtime artifacts.
* Test and evaluation stages verify semantics.
* Publication emits an immutable executable revision.

This prevents the building graph from becoming an unconstrained coding agent. Its creativity operates inside a governed compilation and verification system.
