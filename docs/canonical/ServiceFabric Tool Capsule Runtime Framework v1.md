# ServiceFabric Tool Capsule Runtime Framework v1

**Status:** Architecture baseline
**API version:** `servicefabric.ai/v1alpha1`
**Runtime language:** TypeScript
**MCP production baseline:** `2025-11-25`

---

# 1. Purpose

A **Tool Capsule** is the standard deployable and operable unit through which ServiceFabric exposes a capability to internal graphs, external agent frameworks, and MCP clients.

A capsule combines:

* A canonical `ToolDefinition`
* An immutable tool implementation
* An execution adapter
* Policy enforcement
* Input and output validation
* Maintenance-graph integration
* Telemetry
* Tests and evaluations
* An MCP projection
* Deployment metadata

The capsule is not necessarily a separate container. It is a logical runtime unit that may be deployed:

* As a standalone microservice
* As one operation within a domain microservice
* As an internal graph
* As an adapter to an external API
* As an adapter to another MCP server
* As a local function in a trusted runtime

```text
ToolDefinition
      │
      ▼
 Tool Capsule
 ├── Contract
 ├── Implementation
 ├── Execution adapter
 ├── Policy layer
 ├── Maintenance graph
 ├── Telemetry
 ├── Evaluations
 └── MCP adapter
      │
      ▼
External and internal callers
```

---

# 2. Architectural principles

## 2.1 One canonical invocation model

MCP, REST, internal graphs, scheduled jobs, and tests must all call the same internal capsule interface.

```text
MCP call ────────────┐
REST call ───────────┤
Internal graph call ─┼──► ToolInvocationPipeline
Scheduled call ──────┤
Evaluation call ─────┘
```

Protocol adapters must not implement tool business logic.

## 2.2 Policy enforcement occurs before implementation execution

The implementation must never be responsible for deciding whether a caller is authorized to invoke it.

```text
Caller
  ↓
Verified identity
  ↓
Authorization
  ↓
Approval and effect policy
  ↓
Input validation
  ↓
Implementation
```

The tool implementation may perform additional domain-level validation, but it cannot weaken platform policy.

## 2.3 Tool output is untrusted until validated

A successful HTTP response, database query, model response, or provider result does not automatically constitute a successful tool result.

The capsule must validate:

* Output schema
* Business invariants
* Provenance requirements
* Side-effect evidence
* Quality thresholds
* Provider-response integrity

## 2.4 The maintenance graph surrounds execution

Agentic backing does not replace the implementation.

```text
Maintenance graph
    before-call hooks
          ↓
Tool implementation
          ↓
Maintenance graph
    after-call hooks
```

The maintenance graph may:

* Reformulate an input
* Select a provider
* Retry a transient failure
* Fall back to another implementation
* Validate evidence
* Classify partial success

It must not silently change the externally declared semantics of the tool.

## 2.5 Protocol capabilities are negotiated

MCP clients and servers negotiate supported features during initialization. ServiceFabric must not assume that a client supports optional capabilities such as elicitation, sampling, progress notifications, or dynamic list-change notifications merely because ServiceFabric itself supports them.

## 2.6 Remote and local MCP deployments use different transports

ServiceFabric should use:

* **Streamable HTTP** for remotely hosted MCP servers
* **stdio** for local processes launched directly by an MCP host

These are the standard transports in the stable MCP specification.

---

# 3. Runtime topology

```text
                        External agent framework
                                  │
                             MCP client
                                  │
                       Streamable HTTP / stdio
                                  │
                    ┌─────────────▼─────────────┐
                    │ ServiceFabric MCP Gateway │
                    └─────────────┬─────────────┘
                                  │
                       Protocol normalization
                                  │
                    ┌─────────────▼─────────────┐
                    │ Tool Invocation Runtime   │
                    ├───────────────────────────┤
                    │ Registry resolution       │
                    │ Identity verification     │
                    │ Authorization             │
                    │ Approval                  │
                    │ Validation                │
                    │ Budget enforcement        │
                    │ Maintenance graph         │
                    │ Execution adapter         │
                    │ Output verification       │
                    │ Audit and telemetry       │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┼────────────────────┐
              │                   │                    │
       Native service       Internal graph      Federated MCP
              │                   │                    │
       Domain capability    Agent-backed tool    Third-party tools
```

---

# 4. Repository structure

A ServiceFabric monorepository should separate platform runtime code from individual capsules.

```text
servicefabric/
│
├── apps/
│   ├── mcp-gateway/
│   ├── tool-registry/
│   ├── graph-runtime/
│   ├── policy-service/
│   ├── evaluation-runner/
│   └── operations-console/
│
├── packages/
│   ├── tool-contracts/
│   ├── capsule-runtime/
│   ├── capsule-sdk/
│   ├── mcp-adapter/
│   ├── graph-adapter/
│   ├── policy-client/
│   ├── registry-client/
│   ├── telemetry/
│   ├── schema-validation/
│   ├── error-model/
│   └── testing/
│
├── capsules/
│   ├── math.calculate/
│   ├── research.search-papers/
│   ├── web.search-pages/
│   └── finance.retrieve-filing/
│
├── graphs/
│   ├── building/
│   ├── evolution/
│   └── maintenance/
│
├── policies/
│   ├── authorization/
│   ├── approvals/
│   ├── data-classification/
│   ├── network/
│   └── effects/
│
├── evaluations/
│   ├── tool-selection/
│   ├── argument-construction/
│   ├── result-interpretation/
│   ├── security/
│   └── regression/
│
├── schemas/
│   ├── tool-definition.schema.json
│   ├── tool-revision.schema.json
│   ├── tool-deployment.schema.json
│   └── tool-status.schema.json
│
└── infrastructure/
    ├── containers/
    ├── kubernetes/
    ├── terraform/
    └── observability/
```

A capsule directory should follow this layout:

```text
capsules/research.search-papers/
│
├── manifest/
│   └── tool.yaml
│
├── src/
│   ├── index.ts
│   ├── implementation.ts
│   ├── types.ts
│   ├── domain-validation.ts
│   └── provider-mapping.ts
│
├── maintenance/
│   ├── graph.yaml
│   ├── nodes/
│   └── prompts/
│
├── policies/
│   └── capsule-policy.yaml
│
├── evaluations/
│   ├── selection-cases.yaml
│   ├── invocation-cases.yaml
│   ├── failure-cases.yaml
│   └── adversarial-cases.yaml
│
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── conformance/
│
├── docs/
│   ├── README.md
│   ├── examples.md
│   └── operations.md
│
└── package.json
```

---

# 5. Core invocation types

## 5.1 Invocation request

```typescript
export interface ToolInvocationRequest<TArguments = unknown> {
  invocationId: string;
  toolId: string;
  requestedVersion?: string;
  arguments: TArguments;

  caller: CallerContext;
  protocol: ProtocolContext;
  parent?: ParentExecutionContext;

  requestedAt: string;
  deadline?: string;
  idempotencyKey?: string;

  approval?: ApprovalReference;
}
```

## 5.2 Verified caller context

```typescript
export interface CallerContext {
  principal: {
    id: string;
    type: "user" | "service" | "agent";
    tenantId?: string;
  };

  authenticationMethod: string;
  scopes: string[];
  roles: string[];

  /**
   * True only after identity has been verified by the platform.
   * Caller-supplied identity claims must never set this field.
   */
  verified: boolean;
}
```

ServiceFabric must not authorize a tool based on user identity stated inside natural-language input. MCP guidance similarly warns servers not to treat client-supplied user-identification text as verified identity.

## 5.3 Protocol context

```typescript
export interface ProtocolContext {
  type: "internal" | "mcp" | "rest" | "scheduled" | "evaluation";

  mcp?: {
    protocolVersion: string;
    sessionId?: string;
    clientName?: string;
    clientVersion?: string;

    capabilities: {
      sampling: boolean;
      elicitation: boolean;
      progress: boolean;
      cancellation: boolean;
      listChanged: boolean;
    };
  };
}
```

## 5.4 Parent execution context

```typescript
export interface ParentExecutionContext {
  graphRunId?: string;
  parentInvocationId?: string;
  rootInvocationId?: string;
  depth: number;
  callPath: string[];
}
```

The call path is required to detect:

* Recursive tool calls
* Circular dependencies
* Excessive graph depth
* Tool-call amplification
* Repeated fallback loops

## 5.5 Execution budgets

```typescript
export interface ExecutionBudget {
  maximumDurationMs: number;
  maximumToolCalls: number;
  maximumModelCalls: number;
  maximumTokens?: number;
  maximumCostUsd?: number;
  maximumRecursionDepth: number;
}
```

Every invocation receives a budget, even when most values are zero.

A deterministic calculator might receive:

```typescript
const budget: ExecutionBudget = {
  maximumDurationMs: 2_000,
  maximumToolCalls: 0,
  maximumModelCalls: 0,
  maximumTokens: 0,
  maximumCostUsd: 0,
  maximumRecursionDepth: 0,
};
```

An agent-backed research tool might receive:

```typescript
const budget: ExecutionBudget = {
  maximumDurationMs: 20_000,
  maximumToolCalls: 8,
  maximumModelCalls: 2,
  maximumTokens: 8_000,
  maximumCostUsd: 0.10,
  maximumRecursionDepth: 2,
};
```

---

# 6. Tool execution context

```typescript
export interface ToolExecutionContext {
  invocationId: string;
  tool: ResolvedToolRevision;
  caller: CallerContext;
  protocol: ProtocolContext;
  parent?: ParentExecutionContext;

  signal: AbortSignal;
  deadline: Date;
  budget: BudgetController;

  trace: TraceContext;
  logger: StructuredLogger;
  metrics: MetricsRecorder;
  audit: AuditRecorder;

  secrets: SecretResolver;
  resources: ResourceResolver;
  tools: RestrictedToolClient;
  models: RestrictedModelClient;

  approvals: ApprovalService;
  policies: PolicyDecisionContext;

  maintenance: MaintenanceGraphContext;
}
```

The implementation must receive restricted clients rather than global access to:

* Every ServiceFabric tool
* Every configured model
* The entire filesystem
* Unrestricted network access
* All secrets

The runtime constructs these restricted clients from the manifest.

---

# 7. Capsule implementation contract

```typescript
export interface ToolImplementation<
  TArguments,
  TData
> {
  execute(
    arguments_: TArguments,
    context: ToolExecutionContext
  ): Promise<ToolImplementationResult<TData>>;
}
```

```typescript
export interface ToolImplementationResult<TData> {
  data: TData;
  evidence?: EvidenceRecord[];
  warnings?: ToolWarning[];

  /**
   * Provider-level execution metadata.
   * It must not contain credentials or confidential payloads.
   */
  execution?: {
    provider?: string;
    providerRequestId?: string;
    cached?: boolean;
  };
}
```

The implementation does not construct the full public envelope. The runtime adds:

* `status`
* Standard errors
* Invocation metadata
* Tool version
* Duration
* Audit fields
* Validated evidence
* MCP formatting

This prevents each tool from implementing a subtly different contract.

---

# 8. Standard result model

```typescript
export type ToolResult<TData> =
  | ToolSuccess<TData>
  | ToolPartialSuccess<TData>
  | ToolFailure;
```

```typescript
export interface ToolSuccess<TData> {
  status: "success";
  data: TData;
  error: null;
  warnings: ToolWarning[];
  evidence: EvidenceRecord[];
  meta: ToolResultMeta;
}
```

```typescript
export interface ToolPartialSuccess<TData> {
  status: "partial";
  data: TData;
  error: null;
  warnings: ToolWarning[];
  evidence: EvidenceRecord[];
  meta: ToolResultMeta;
}
```

```typescript
export interface ToolFailure {
  status: "error";
  data: null;
  error: ToolError;
  warnings: ToolWarning[];
  evidence: EvidenceRecord[];
  meta: ToolResultMeta;
}
```

```typescript
export interface ToolError {
  code: string;

  category:
    | "validation"
    | "authentication"
    | "authorization"
    | "approval"
    | "policy"
    | "dependency"
    | "timeout"
    | "cancelled"
    | "rate_limit"
    | "business_rule"
    | "quality"
    | "budget"
    | "conflict"
    | "unavailable"
    | "internal";

  message: string;
  retryable: boolean;
  suggestedAction?: string;
  safeDetails?: Record<string, unknown>;
}
```

---

# 9. Stable platform error codes

ServiceFabric should reserve platform error prefixes.

```text
SF-AUTH-*       Authentication and authorization
SF-APPROVAL-*   Approval and consent
SF-VALID-*      Schema and input validation
SF-POLICY-*     Policy decisions
SF-BUDGET-*     Cost, time, model or tool budgets
SF-EXEC-*       Execution failures
SF-DEPEND-*     Dependency failures
SF-OUTPUT-*     Output validation
SF-QUALITY-*    Quality-control failures
SF-MCP-*        MCP adaptation and protocol failures
SF-RUNTIME-*    Runtime and infrastructure
```

Examples:

```text
SF-AUTH-001       Unverified caller
SF-AUTH-002       Missing required scope
SF-APPROVAL-001   Required approval not supplied
SF-VALID-001      Input schema violation
SF-BUDGET-001     Tool-call budget exhausted
SF-BUDGET-002     Invocation deadline exceeded
SF-EXEC-001       Tool implementation failed
SF-DEPEND-001     Required provider unavailable
SF-OUTPUT-001     Output schema violation
SF-QUALITY-001    Provenance coverage below threshold
SF-MCP-001        Unknown MCP tool
SF-RUNTIME-001    Tool revision unavailable
```

Provider-specific messages must be mapped into stable ServiceFabric errors.

---

# 10. Invocation pipeline

Every capsule call follows the same sequence.

```text
 1. Accept request
 2. Establish trace
 3. Resolve tool and revision
 4. Verify tool availability
 5. Verify caller identity
 6. Authorize capability
 7. Classify effects
 8. Obtain or verify approval
 9. Validate input schema
10. Apply domain preconditions
11. Establish budgets and deadline
12. Run maintenance preflight
13. Select execution adapter
14. Execute implementation
15. Recover or fall back where permitted
16. Validate output schema
17. Verify evidence and effects
18. Classify success, partial success, or failure
19. Record audit and telemetry
20. Return protocol projection
```

## 10.1 Pipeline interface

```typescript
export interface ToolInvocationPipeline {
  invoke<TArguments, TData>(
    request: ToolInvocationRequest<TArguments>
  ): Promise<ToolResult<TData>>;
}
```

## 10.2 Pipeline implementation skeleton

```typescript
export class DefaultToolInvocationPipeline
  implements ToolInvocationPipeline
{
  constructor(
    private readonly registry: ToolRegistry,
    private readonly identity: IdentityVerifier,
    private readonly policy: PolicyEngine,
    private readonly approvals: ApprovalService,
    private readonly schemas: SchemaValidator,
    private readonly maintenance: MaintenanceGraphRuntime,
    private readonly adapters: ExecutionAdapterRegistry,
    private readonly telemetry: TelemetryService
  ) {}

  async invoke<TArguments, TData>(
    request: ToolInvocationRequest<TArguments>
  ): Promise<ToolResult<TData>> {
    const startedAt = Date.now();
    const trace = this.telemetry.startInvocation(request);

    try {
      const tool = await this.registry.resolve(
        request.toolId,
        request.requestedVersion
      );

      await this.assertAvailable(tool);
      await this.identity.verify(request.caller);

      const policyDecision = await this.policy.evaluate({
        tool,
        caller: request.caller,
        arguments: request.arguments,
        protocol: request.protocol,
      });

      await this.assertAuthorized(policyDecision);
      await this.approvals.assertSatisfied({
        tool,
        request,
        policyDecision,
      });

      const validatedArguments =
        this.schemas.validateInput<TArguments>(
          tool.interface.inputSchema,
          request.arguments
        );

      const context = this.createExecutionContext({
        request,
        tool,
        policyDecision,
        trace,
      });

      const prepared = await this.maintenance.beforeCall({
        arguments: validatedArguments,
        context,
      });

      const adapter = this.adapters.resolve(
        prepared.executionPlan.adapter
      );

      const rawResult = await adapter.execute<TArguments, TData>({
        arguments: prepared.arguments,
        executionPlan: prepared.executionPlan,
        context,
      });

      const recovered = await this.maintenance.afterExecution({
        result: rawResult,
        context,
      });

      const validatedData =
        this.schemas.validateOutput<TData>(
          tool.interface.outputSchema,
          recovered.data
        );

      const completed = await this.maintenance.afterCall({
        data: validatedData,
        evidence: recovered.evidence,
        warnings: recovered.warnings,
        context,
      });

      return this.buildSuccessResult(
        completed,
        tool,
        request,
        startedAt
      );
    } catch (error: unknown) {
      return this.handleFailure(
        error,
        request,
        trace,
        startedAt
      );
    } finally {
      trace.end();
    }
  }
}
```

---

# 11. Pipeline interceptors

The runtime should implement cross-cutting behaviour as ordered interceptors.

```typescript
export interface ToolInterceptor {
  name: string;
  order: number;

  invoke<TArguments, TData>(
    context: InvocationPipelineContext<TArguments>,
    next: ToolInvocationNext<TArguments, TData>
  ): Promise<ToolResult<TData>>;
}
```

Recommended default order:

```text
010  TraceInterceptor
020  RegistryResolutionInterceptor
030  AvailabilityInterceptor
040  IdentityInterceptor
050  AuthorizationInterceptor
060  ApprovalInterceptor
070  InputValidationInterceptor
080  DataClassificationInterceptor
090  BudgetInterceptor
100  IdempotencyInterceptor
110  MaintenancePreflightInterceptor
120  ExecutionInterceptor
130  MaintenanceRecoveryInterceptor
140  OutputValidationInterceptor
150  EvidenceValidationInterceptor
160  EffectVerificationInterceptor
170  ResultClassificationInterceptor
180  AuditInterceptor
190  MetricsInterceptor
200  ProtocolProjectionInterceptor
```

The order should be platform-controlled rather than configurable by individual tools.

A capsule may add domain interceptors only in designated extension zones:

```text
After input schema validation
Before implementation execution
After implementation execution
Before final output projection
```

---

# 12. Execution adapters

Every implementation type is accessed through a common adapter contract.

```typescript
export interface ExecutionAdapter {
  readonly type: ExecutionAdapterType;

  execute<TArguments, TData>(
    request: AdapterExecutionRequest<TArguments>
  ): Promise<ToolImplementationResult<TData>>;
}
```

```typescript
export type ExecutionAdapterType =
  | "native_function"
  | "native_service"
  | "internal_graph"
  | "external_http"
  | "database_operation"
  | "command_runner"
  | "federated_mcp"
  | "human_task";
```

## 12.1 Native function adapter

Used for:

* Calculators
* Parsers
* Formatters
* Deterministic transformations
* Lightweight validation

Constraints:

* No implicit network access
* No global mutable state
* Strict runtime timeout
* Sandboxed where code provenance is uncertain

## 12.2 Native service adapter

Used when the implementation lives in another ServiceFabric microservice.

```typescript
export interface NativeServiceTarget {
  service: string;
  operation: string;
  protocol: "http" | "grpc" | "message";
  endpointRef: string;
}
```

Responsibilities:

* Service discovery
* Mutual authentication
* Deadline propagation
* Trace propagation
* Error normalization
* Circuit breaking

## 12.3 Internal graph adapter

Used for genuinely multi-step agent-backed tools.

```typescript
export interface InternalGraphTarget {
  graphId: string;
  graphVersion: string;
  entryNode: string;
}
```

The graph receives only the tools and models explicitly permitted in the manifest.

## 12.4 External HTTP adapter

Used for tightly bounded third-party APIs.

Requirements:

* Allowlisted destination
* Defined request mapping
* Defined response mapping
* Secret isolation
* Timeout
* Rate-limit handling
* Response-size limit
* Content-type validation
* SSRF controls

## 12.5 Federated MCP adapter

Used when wrapping a third-party MCP server.

```text
External graph
    ↓
ServiceFabric public tool
    ↓
ServiceFabric policy and maintenance
    ↓
Federated MCP adapter
    ↓
Third-party MCP server
```

ServiceFabric should not expose third-party tools directly without normalization.

The adapter must provide:

* Tool-name mapping
* Input-schema compatibility checks
* Output validation
* Authentication isolation
* Risk reclassification
* Stable ServiceFabric errors
* Provider-health monitoring
* Version-drift detection
* Tool-list change handling

MCP allows tool inventories to change and supports list-change notifications where negotiated. The registry should invalidate cached federated tool definitions when such a notification is received.

## 12.6 Command-runner adapter

Used for:

* Compilers
* Test runners
* Linters
* Build tools
* Data-processing commands

It must execute in a sandbox with:

* Ephemeral filesystem
* Restricted network
* CPU limit
* Memory limit
* Time limit
* Process-count limit
* Output-size limit
* Explicit mounted resources
* No inherited host secrets

## 12.7 Human-task adapter

Used when execution must be assigned to a person.

Examples:

* Legal review
* Transaction approval
* Manual data confirmation
* Procurement evaluation
* Management decision

The initial call should normally return:

```json
{
  "status": "partial",
  "data": {
    "taskId": "human-task-reference",
    "state": "awaiting_human"
  },
  "error": null
}
```

Long-running human tasks should not keep an MCP HTTP request open.

---

# 13. Maintenance graph interface

The maintenance graph is divided into explicit hooks.

```typescript
export interface MaintenanceGraphRuntime {
  beforeCall<TArguments>(
    request: MaintenanceBeforeCallRequest<TArguments>
  ): Promise<MaintenancePreparedCall<TArguments>>;

  afterExecution<TData>(
    request: MaintenanceAfterExecutionRequest<TData>
  ): Promise<MaintenanceRecoveredResult<TData>>;

  afterCall<TData>(
    request: MaintenanceAfterCallRequest<TData>
  ): Promise<MaintenanceCompletedResult<TData>>;

  onFailure(
    request: MaintenanceFailureRequest
  ): Promise<MaintenanceFailureDecision>;
}
```

## 13.1 Before-call responsibilities

Permitted activities:

* Normalize arguments
* Resolve defaults
* Check domain preconditions
* Select provider
* Check dependency health
* Establish execution plan
* Reserve budget
* Check cache
* Detect duplicate requests
* Determine whether progress reporting is useful

Prohibited activities:

* Expanding caller permissions
* Downgrading approval requirements
* Changing the declared effect class
* Accessing undeclared tools
* Hiding policy violations

## 13.2 After-execution responsibilities

Permitted activities:

* Retry a transient failure
* Select a declared fallback
* Merge results
* Remove duplicates
* Validate identifiers
* Check business invariants
* Convert provider output
* Recover partial data

## 13.3 After-call responsibilities

Permitted activities:

* Attach provenance
* Classify partial success
* Generate safe warnings
* Calculate quality indicators
* Record provider performance
* Update `ToolStatus`
* Emit an evolution trigger

## 13.4 Failure decisions

```typescript
export type MaintenanceFailureDecision =
  | {
      action: "return_error";
      error: ToolError;
    }
  | {
      action: "retry";
      delayMs: number;
      executionPlan?: ExecutionPlan;
    }
  | {
      action: "fallback";
      executionPlan: ExecutionPlan;
    }
  | {
      action: "return_partial";
      data: unknown;
      warnings: ToolWarning[];
      evidence: EvidenceRecord[];
    }
  | {
      action: "quarantine";
      error: ToolError;
      incident: IncidentDraft;
    };
```

---

# 14. Maintenance graph state machine

```text
RECEIVED
   ↓
POLICY_VERIFIED
   ↓
INPUT_VALIDATED
   ↓
DEPENDENCIES_CHECKED
   ↓
EXECUTION_PLANNED
   ↓
EXECUTING
   ├── SUCCESS
   ├── PARTIAL
   └── FAILURE
          ↓
    FAILURE_CLASSIFIED
      ├── RETRY
      ├── FALLBACK
      ├── REPAIR
      ├── RETURN_ERROR
      └── QUARANTINE
   ↓
OUTPUT_VALIDATED
   ↓
EVIDENCE_VALIDATED
   ↓
COMPLETION_CLASSIFIED
   ↓
RECORDED
```

The graph must persist only the state necessary for:

* Recovery
* Auditing
* Idempotency
* Status updates

It should not retain full sensitive request and response payloads unless retention policy explicitly allows this.

---

# 15. Provider routing

Provider selection should be separated from public tool selection.

The external caller chooses:

```text
research.search_papers
```

The maintenance graph chooses:

```text
arXiv
Crossref
Semantic Scholar
internal index
cached result
```

```typescript
export interface ProviderCandidate {
  id: string;
  healthy: boolean;
  supports: string[];

  estimatedLatencyMs: number;
  estimatedCostUsd: number;

  qualityScore: number;
  freshnessScore: number;
  trustScore: number;

  rateLimitRemaining?: number;
}
```

A routing decision may use:

```typescript
export interface ProviderRoutingWeights {
  quality: number;
  freshness: number;
  latency: number;
  cost: number;
  trust: number;
}
```

Provider routing must remain deterministic enough to audit. The decision record should explain:

```json
{
  "selectedProvider": "crossref",
  "reasonCodes": [
    "SUPPORTS_DATE_FILTER",
    "HEALTHY",
    "LOWER_EXPECTED_LATENCY",
    "WITHIN_COST_BUDGET"
  ]
}
```

An LLM should not be the sole mechanism selecting security-sensitive providers.

---

# 16. Agentic backing boundaries

A capsule with model access must define a restricted model interface.

```typescript
export interface RestrictedModelClient {
  generateStructured<TOutput>(
    request: {
      purpose: string;
      input: unknown;
      outputSchema: object;
      maximumTokens: number;
    }
  ): Promise<TOutput>;
}
```

The model client must enforce:

* Allowed purposes
* Output schema
* Token budget
* Cost budget
* Data-classification policy
* Approved provider
* No undeclared tool access
* Trace linkage

## 16.1 No invisible autonomy

An agent-backed tool must declare:

* Why a model is necessary
* Which decisions it may make
* Which decisions remain deterministic
* Which internal tools it may call
* Maximum calls
* Maximum recursion depth
* Completion criteria
* Evidence requirements

## 16.2 Sampling abstraction

MCP sampling can allow a server to request model assistance from a client, but this is an optional negotiated client capability. ServiceFabric should therefore expose an internal abstraction:

```typescript
export interface ModelAssistanceProvider {
  requestStructuredAssistance<T>(
    request: AssistanceRequest
  ): Promise<T>;
}
```

The runtime may implement it through:

* A ServiceFabric-managed model
* MCP sampling, where negotiated
* A local model
* A policy-approved external model

Tool implementations should not depend directly on MCP sampling.

## 16.3 Elicitation abstraction

Where more information is necessary, a tool may request clarification through:

```typescript
export interface ElicitationProvider {
  request<T>(
    request: ElicitationRequest<T>
  ): Promise<ElicitationResult<T>>;
}
```

The runtime may implement this through:

* MCP elicitation, where negotiated
* The parent agent graph
* A user-interface workflow
* A human task

When elicitation is unavailable, the tool must follow its declared fallback:

* Return a recoverable validation error
* Use a safe default
* Return partial results
* Escalate to the parent graph

---

# 17. Approval and side-effect handling

Tools with external effects must support a preparation phase before execution.

```text
Intent
  ↓
Validate proposed action
  ↓
Produce action preview
  ↓
Obtain approval
  ↓
Revalidate state
  ↓
Commit action
  ↓
Verify effect
  ↓
Return receipt
```

## 17.1 Action preview

```typescript
export interface ActionPreview {
  toolId: string;
  effectClass: string;

  summary: string;
  target: string;
  changes: ProposedChange[];

  reversible: boolean;
  estimatedCost?: MonetaryAmount;

  expiresAt: string;
  previewHash: string;
}
```

## 17.2 Approval reference

```typescript
export interface ApprovalReference {
  approvalId: string;
  previewHash: string;
  approvedBy: string;
  approvedAt: string;
  expiresAt: string;
}
```

The preview hash prevents approval for one action from being reused for a modified action.

## 17.3 Revalidation

Immediately before committing an action, the runtime must verify:

* Approval remains valid
* Arguments still match the preview
* Target state has not changed materially
* Idempotency key has not already been consumed
* Policy still permits execution
* Tool revision has not changed unexpectedly

## 17.4 Effect receipt

```typescript
export interface EffectReceipt {
  effectId: string;
  committedAt: string;
  target: string;
  operation: string;
  resultState?: string;
  reversible: boolean;
  rollbackToolId?: string;
  providerReference?: string;
}
```

A state-changing tool cannot return success without evidence that the effect was accepted or committed.

---

# 18. Input validation layers

Validation should occur in four layers.

```text
Layer 1: Protocol validation
Layer 2: JSON Schema validation
Layer 3: Domain validation
Layer 4: Policy validation
```

## 18.1 Protocol validation

Examples:

* Valid MCP request
* Tool name present
* Arguments object present
* Supported protocol version

## 18.2 Schema validation

Examples:

* Required fields
* Types
* Formats
* Bounds
* Enumerations
* No undeclared properties

## 18.3 Domain validation

Examples:

* Start date precedes end date
* Financial instrument exists
* Currency pair is supported
* Repository path exists
* Requested operation is meaningful

## 18.4 Policy validation

Examples:

* Data can leave the organization
* Caller may access the account
* Model use is permitted
* External provider is approved
* Transaction value is within limits

---

# 19. Output and evidence validation

## 19.1 Output schema

Native ServiceFabric tools must define structured outputs. Under the stable MCP specification, when a tool declares an output schema, the server must provide structured results conforming to it, and clients should validate those results.

## 19.2 Evidence records

```typescript
export interface EvidenceRecord {
  type:
    | "source"
    | "calculation"
    | "execution"
    | "effect_receipt"
    | "test_result"
    | "human_confirmation";

  source: string;
  locator?: string;
  retrievedAt?: string;

  contentHash?: string;
  providerReference?: string;

  confidence?: number;
}
```

## 19.3 Evidence requirements by tool class

| Tool class             | Required evidence                                     |
| ---------------------- | ----------------------------------------------------- |
| Pure computation       | Formula or calculation trace where useful             |
| External retrieval     | Source and retrieval time                             |
| Database read          | Dataset/table reference and snapshot where applicable |
| Code execution         | Command, exit status and logs                         |
| File mutation          | Changed path and content hash                         |
| External communication | Provider message identifier                           |
| Financial action       | Transaction identifier and state                      |
| Human task             | Confirming actor and timestamp                        |

## 19.4 Result quality states

```text
valid
valid_with_warnings
partial
invalid_recoverable
invalid_terminal
suspicious
```

A suspicious result may trigger:

* Secondary verification
* Provider comparison
* Human review
* Tool quarantine
* Evolution analysis

---

# 20. MCP gateway

The MCP gateway projects registered Tool Capsules as MCP tools.

```typescript
export interface McpToolProjection {
  name: string;
  title?: string;
  description: string;
  inputSchema: object;
  outputSchema?: object;
  annotations?: Record<string, unknown>;
  execution?: Record<string, unknown>;
  _meta?: Record<string, unknown>;
}
```

## 20.1 Tool discovery

```text
MCP tools/list
    ↓
Authenticate caller
    ↓
Load active tool revisions
    ↓
Filter by caller authorization
    ↓
Generate MCP projections
    ↓
Return paginated tool list
```

The gateway should not list tools the authenticated caller can never use.

Tools that might become usable after separate approval may remain discoverable if the description clearly states the approval requirement.

## 20.2 Tool invocation

```text
MCP tools/call
    ↓
Resolve MCP name to ServiceFabric tool ID
    ↓
Construct ToolInvocationRequest
    ↓
Call canonical ToolInvocationPipeline
    ↓
Project ToolResult into CallToolResult
```

MCP tools are discovered through `tools/list` and invoked through `tools/call`.

## 20.3 Result projection

```typescript
export function toMcpResult<T>(
  result: ToolResult<T>
): {
  content: Array<{ type: "text"; text: string }>;
  structuredContent: ToolResult<T>;
  isError: boolean;
} {
  return {
    content: [
      {
        type: "text",
        text: summarizeToolResult(result),
      },
    ],
    structuredContent: result,
    isError: result.status === "error",
  };
}
```

## 20.4 Protocol errors versus tool errors

The MCP adapter should return a protocol-level JSON-RPC error for:

* Unknown tool
* Invalid JSON-RPC request
* Unsupported MCP method
* Uninitialized session
* Fundamental server failure before an invocation is created

It should return a normal tool result with `isError: true` for:

* Invalid tool arguments
* Authorization denial after tool resolution
* Provider failure
* Rate limit
* Domain validation
* Timeout
* Quality failure

This allows calling agents to inspect and possibly repair tool-level failures.

---

# 21. MCP transport deployment

## 21.1 Remote server

```text
Client
  ↓ HTTPS
API gateway / load balancer
  ↓
MCP Streamable HTTP endpoint
  ↓
ServiceFabric MCP gateway
```

Requirements:

* HTTPS
* Authentication
* Origin validation
* Request-size limits
* Session controls where applicable
* Rate limiting
* Connection limits
* Audit logging
* No token passthrough
* Resource-specific token validation

MCP transport guidance requires Origin validation for Streamable HTTP to mitigate DNS-rebinding risks and recommends binding local servers to localhost rather than all interfaces.

## 21.2 Local server

```text
MCP host
  ↓ child process
ServiceFabric local adapter
  ↓ stdio
Tool Capsule runtime
```

Requirements:

* Bind no network port by default
* Write only MCP messages to stdout
* Write logs to stderr
* Restrict filesystem access
* Restrict inherited environment variables
* Terminate with the host process

## 21.3 Session policy

ServiceFabric tools should be stateless by default.

Session state should be introduced only when required for:

* Long-running workflows
* Explicit user interaction
* Resource subscriptions
* Stateful external systems
* Resumable execution

Business state should not be stored only in MCP transport sessions.

---

# 22. Security interceptors

Every remote capsule invocation should pass through these controls.

```text
Transport authentication
       ↓
Token audience validation
       ↓
Verified principal construction
       ↓
Tool authorization
       ↓
Data classification
       ↓
Effect and approval policy
       ↓
Network and secret restrictions
       ↓
Execution
```

MCP’s security guidance identifies risks including token passthrough, confused-deputy scenarios, SSRF, session hijacking and insufficient token-audience validation. ServiceFabric should treat MCP authentication as one layer within its broader zero-trust authorization design.

## 22.1 Token passthrough prohibition

A token received from an MCP client must not be forwarded unchanged to a third-party provider.

Instead:

```text
Client token
    ↓
Validate for ServiceFabric
    ↓
Authorize ServiceFabric tool
    ↓
Use ServiceFabric provider credential
       or delegated provider-specific token
```

## 22.2 Prompt-injection boundary

Content retrieved by a tool is data, not policy.

External content may not:

* Add tool permissions
* Request secret disclosure
* Alter budgets
* Suppress logging
* Authorize side effects
* Override the maintenance graph
* Change the caller identity
* Invoke undeclared internal tools

---

# 23. Tool registry integration

The capsule runtime obtains an immutable `ResolvedToolRevision`.

```typescript
export interface ResolvedToolRevision {
  definition: ToolDefinition;
  revisionId: string;
  contentHash: string;
  lifecycleState: "active" | "degraded";

  implementation: {
    artifactRef: string;
    adapter: ExecutionAdapterType;
  };

  interface: {
    inputSchema: object;
    outputSchema: object;
  };

  policyBundleRef: string;
  evaluationReportRef: string;
  maintenanceGraphRef: string;
}
```

The registry must resolve:

* Exact active revision
* Compatible version
* Tenant visibility
* Environment
* Authorization visibility
* Deprecation state
* Deployment health

Resolution must remain stable throughout one invocation.

A deployment must not change revisions halfway through a call.

---

# 24. Idempotency and concurrency

## 24.1 Idempotency classes

```text
naturally_idempotent
keyed_idempotent
non_idempotent
unknown
```

## 24.2 Idempotency record

```typescript
export interface IdempotencyRecord {
  toolId: string;
  toolRevision: string;
  callerId: string;
  key: string;

  argumentHash: string;
  state: "in_progress" | "completed" | "failed";

  resultReference?: string;
  createdAt: string;
  expiresAt: string;
}
```

For state-changing tools:

* Reusing a key with identical arguments should return the original result.
* Reusing a key with different arguments should return a conflict.
* A retry must not duplicate the side effect.

## 24.3 Concurrency keys

Some tools require serialized execution by:

* Account
* File
* Repository
* Project
* Transaction
* Calendar event
* Deployment environment

```yaml
concurrency:
  keyExpression: arguments.accountId
  maximumPerKey: 1
```

---

# 25. Caching

Caching should occur after authorization but before external execution.

```text
Authenticate
  ↓
Authorize
  ↓
Validate
  ↓
Calculate cache key
  ↓
Check policy-compatible cache
  ↓
Return or execute
```

A cache entry must include:

* Tool revision
* Argument hash
* Data-classification level
* Authorization scope fingerprint
* Provider
* Creation time
* Expiration
* Evidence
* Freshness metadata

Results must not be shared across callers when authorization or underlying data visibility differs.

---

# 26. Cancellation and progress

## 26.1 Cancellation

The runtime should propagate an `AbortSignal` through:

```text
MCP request
  ↓
Invocation pipeline
  ↓
Maintenance graph
  ↓
Execution adapter
  ↓
Provider or child process
```

Cancellation does not imply rollback. State-changing tools must separately describe whether cancellation:

* Prevents execution
* Stops execution before commit
* Leaves the effect uncertain
* Initiates compensating action

## 26.2 Progress

Progress should be used for:

* Long research workflows
* Repository analysis
* Large file processing
* Test suites
* Data pipelines
* Multi-provider retrieval

Progress events should report stable stages rather than invented percentages:

```json
{
  "stage": "provider_search",
  "completedUnits": 2,
  "totalUnits": 3,
  "message": "Two of three scholarly providers completed."
}
```

Progress should only be sent through MCP when the client negotiated support.

---

# 27. Telemetry

## 27.1 Trace structure

```text
tool.invoke
├── registry.resolve
├── identity.verify
├── policy.evaluate
├── approval.verify
├── schema.validate_input
├── maintenance.before_call
├── provider.select
├── adapter.execute
│   ├── dependency.call
│   └── dependency.parse
├── maintenance.after_execution
├── schema.validate_output
├── evidence.validate
├── maintenance.after_call
└── protocol.project
```

## 27.2 Core metrics

```text
tool_invocations_total
tool_success_total
tool_partial_success_total
tool_errors_total
tool_latency_ms
tool_queue_time_ms
tool_policy_denials_total
tool_approval_requests_total
tool_input_validation_failures_total
tool_output_validation_failures_total
tool_retries_total
tool_fallbacks_total
tool_cost_usd
tool_model_calls_total
tool_internal_calls_total
tool_cache_hit_rate
tool_quarantine_events_total
```

## 27.3 Quality metrics

```text
tool_agent_selection_precision
tool_agent_selection_recall
tool_argument_validity_rate
tool_result_interpretation_rate
tool_evidence_coverage
tool_provider_agreement_rate
tool_hallucination_rate
tool_recovery_success_rate
```

---

# 28. Capsule testing framework

Every capsule requires six testing layers.

## 28.1 Unit tests

Test:

* Domain logic
* Provider mappings
* Input normalization
* Error mappings
* Result classification

## 28.2 Contract tests

Test:

* Manifest validity
* Input schema
* Output schema
* Standard envelope
* Stable error codes

## 28.3 Integration tests

Test:

* Service calls
* Providers
* Databases
* Graph execution
* Authentication
* Policy service

## 28.4 Maintenance tests

Test:

* Retry conditions
* Fallback selection
* Partial success
* Deadline handling
* Budget exhaustion
* Circuit breaking

## 28.5 Agent-callability tests

Test whether models and graphs:

* Select the tool appropriately
* Avoid it when inappropriate
* Build valid arguments
* Interpret warnings
* Repair validation errors
* Respect approval requirements

## 28.6 MCP conformance tests

Test:

* Initialization
* Capability negotiation
* `tools/list`
* `tools/call`
* Structured output
* Execution errors
* Cancellation
* Dynamic tool-list changes
* stdio and Streamable HTTP deployments

The official MCP Inspector can be incorporated as an interactive development and debugging layer for stdio, SSE and Streamable HTTP connections.

---

# 29. Capsule SDK

The ServiceFabric Capsule SDK should make the safe path the easiest path.

```typescript
export function defineTool<TArguments, TData>(
  definition: ToolDefinitionConfig<TArguments, TData>,
  implementation: ToolImplementation<TArguments, TData>
): ToolCapsule<TArguments, TData>;
```

Example:

```typescript
import { defineTool } from "@servicefabric/capsule-sdk";
import { z } from "zod";

const Arguments = z.object({
  expression: z.string().min(1).max(2_000),
});

const Data = z.object({
  result: z.number(),
});

export const calculateTool = defineTool(
  {
    id: "math.calculate",
    version: "1.0.0",
    title: "Mathematical Calculator",

    inputSchema: Arguments,
    dataSchema: Data,

    behavior: {
      capabilityClass: "computation",
      determinism: "deterministic",
      statefulness: "stateless",
    },

    effects: {
      class: "pure",
      idempotent: true,
      destructive: false,
      openWorld: false,
    },

    agenticBacking: {
      level: "guarded",
      modelUse: false,
      internalTools: [],
    },

    timeoutMs: 2_000,
  },

  {
    async execute(arguments_, context) {
      context.signal.throwIfAborted();

      const result = safeEvaluateExpression(
        arguments_.expression
      );

      return {
        data: { result },
      };
    },
  }
);
```

The SDK should automatically provide:

* Schema compilation
* Standard result envelope
* Trace creation
* Logging
* Error normalization
* Deadline handling
* MCP projection
* Manifest validation
* Test harnesses

---

# 30. MCP adapter example

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { toMcpResult } from "@servicefabric/mcp-adapter";

export function registerServiceFabricTools(
  server: McpServer,
  registry: ToolRegistry,
  pipeline: ToolInvocationPipeline
): void {
  for (const tool of registry.listMcpExposedTools()) {
    server.registerTool(
      tool.mcp.name,
      {
        title: tool.mcp.title,
        description: tool.mcp.description,
        inputSchema: tool.inputSchema,
        outputSchema: tool.outputSchema,
        annotations: tool.mcp.annotations,
      },
      async (arguments_, extra) => {
        const result = await pipeline.invoke({
          invocationId: createInvocationId(),
          toolId: tool.id,
          requestedVersion: tool.version,
          arguments: arguments_,

          caller: buildVerifiedCallerContext(extra),
          protocol: buildMcpProtocolContext(extra),

          requestedAt: new Date().toISOString(),
          deadline: deriveDeadline(extra),
        });

        return toMcpResult(result);
      }
    );
  }
}
```

The official TypeScript SDK exposes server-side tool registration and supports structured content and output schemas. The current SDK guidance uses Streamable HTTP for remote servers and stdio for local integrations.

The exact SDK import paths should remain isolated inside `packages/mcp-adapter` because SDK package structure may change between major versions.

---

# 31. Capsule deployment modes

## 31.1 Shared runtime

Multiple low-risk tools run in one process.

Suitable for:

* Calculators
* Formatting
* Parsing
* Small deterministic functions

Benefits:

* Low overhead
* Fast startup
* Shared infrastructure

Risks:

* Reduced fault isolation
* Shared resource limits
* Larger blast radius

## 31.2 Dedicated service

One tool or related tool family runs in a dedicated service.

Suitable for:

* Financial systems
* Sensitive data
* High-throughput tools
* Tools with specialized dependencies
* Tools requiring independent scaling

## 31.3 Graph-backed service

A dedicated graph runtime executes the capability.

Suitable for:

* Research synthesis
* Software investigation
* Project planning
* Organisational analysis

## 31.4 Federated service

ServiceFabric wraps an external MCP or API provider.

Suitable for:

* Third-party search
* SaaS integrations
* External productivity systems
* Vendor-specific data sources

---

# 32. Runtime health model

```typescript
export interface ToolStatus {
  toolId: string;
  revisionId: string;

  state:
    | "healthy"
    | "degraded"
    | "unavailable"
    | "quarantined"
    | "deprecated";

  checks: {
    implementation: HealthState;
    dependencies: HealthState;
    policy: HealthState;
    maintenanceGraph: HealthState;
    evaluations: HealthState;
  };

  metrics: {
    successRate: number;
    errorRate: number;
    p95LatencyMs: number;
    outputValidityRate: number;
    qualityScore?: number;
  };

  updatedAt: string;
}
```

## 32.1 Availability rules

A tool is:

* **Healthy** when all mandatory checks pass.
* **Degraded** when it can return valid but reduced results.
* **Unavailable** when it cannot satisfy its contract.
* **Quarantined** when continued operation may be unsafe or misleading.
* **Deprecated** when supported temporarily but scheduled for retirement.

---

# 33. Tool Capsule invariants

```text
SF-C001  Every invocation uses the canonical pipeline.
SF-C002  Protocol adapters contain no business logic.
SF-C003  Every caller identity is verified before authorization.
SF-C004  Every tool revision remains immutable during execution.
SF-C005  Every input is schema-validated before implementation.
SF-C006  Every output is schema-validated before return.
SF-C007  Every external effect requires effect verification.
SF-C008  Every agent-backed tool has explicit budgets.
SF-C009  Every internal tool dependency is allowlisted.
SF-C010  Every model purpose is declared.
SF-C011  Every external network destination is policy-controlled.
SF-C012  No client token is passed unchanged to another service.
SF-C013  External content cannot modify platform policy.
SF-C014  Every retry follows declared retry policy.
SF-C015  Every fallback is declared in the manifest.
SF-C016  Every invocation has a deadline.
SF-C017  Every invocation has a correlation identifier.
SF-C018  Every state-changing call supports idempotency policy.
SF-C019  Every tool-level failure has a stable error code.
SF-C020  Every active capsule has a maintenance graph.
SF-C021  Every MCP projection is generated from the canonical manifest.
SF-C022  Every deployed capsule has an evaluation report.
SF-C023  Every federated tool is revalidated by ServiceFabric.
SF-C024  Every tool call records an auditable policy decision.
SF-C025  No tool may silently expand its declared effects.
```

---

# 34. Reference invocation: `research.search_papers`

```text
1. External graph calls research.search_papers
2. MCP gateway authenticates the connection
3. Registry resolves revision 1.0.3
4. Authorization checks research.read
5. Input schema validates the query and date filters
6. Budget controller assigns:
     - 20 seconds
     - 8 internal calls
     - 2 model calls
     - $0.10
7. Maintenance preflight:
     - normalizes the query
     - checks provider health
     - chooses Crossref and arXiv
8. Native service adapter performs searches
9. One provider times out
10. Maintenance graph classifies the failure as transient
11. Declared fallback provider is called
12. Results are merged and deduplicated
13. DOI identifiers are validated
14. Output schema is validated
15. Provenance coverage is checked
16. Result is classified as success or partial
17. Provider health and quality telemetry are recorded
18. MCP adapter returns:
     - concise text content
     - structuredContent
     - isError: false
```

---

# 35. Reference invocation: `project.create_task`

```text
1. External graph calls project.create_task
2. Identity and project scopes are verified
3. Tool effects are classified as write_reversible
4. Runtime generates an action preview
5. Approval policy is evaluated
6. Approval is obtained or verified
7. Arguments are revalidated against the preview hash
8. Idempotency key is reserved
9. Provider adapter creates the task
10. Provider returns a task identifier
11. Maintenance graph verifies the created task
12. Effect receipt is attached
13. Audit record is written
14. Structured success result is returned
```

---

# 36. Architectural decision

ServiceFabric should implement Tool Capsules around five stable internal boundaries:

```text
ToolDefinition
      ↓
ToolInvocationPipeline
      ↓
MaintenanceGraphRuntime
      ↓
ExecutionAdapter
      ↓
ToolResult
```

MCP remains outside these boundaries:

```text
MCP request
     ↓
MCP adapter
     ↓
Canonical ServiceFabric invocation
     ↓
MCP result projection
```

This allows ServiceFabric to:

* Evolve independently of MCP SDK implementation details
* Support additional protocols
* Apply one security model to every tool
* Reuse maintenance graphs
* Normalize third-party providers
* Test tools without an MCP transport
* Preserve stable agent-facing semantics
* Replace implementations without changing callers
* Scale primitive and agent-backed tools within one framework
