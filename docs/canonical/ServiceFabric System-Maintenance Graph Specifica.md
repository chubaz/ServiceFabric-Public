# ServiceFabric System-Maintenance Graph Specification v1

**Status:** Architecture baseline
**Graph family:** `system-maintenance`
**Default invocation graph:** `standard-tool-maintenance`
**Default operational graph:** `standard-tool-operations`
**API version:** `servicefabric.ai/v1alpha1`
**MCP production profile:** `2025-11-25`

---

# 1. Purpose

The **System-Maintenance Graph** provides the operational and agentic backing required to support a ServiceFabric tool after it has been built and published.

It has two responsibilities:

```text id="5ovl8g"
Invocation maintenance
    Supports an individual external tool call

Operational maintenance
    Maintains the capability between calls
```

Together, they ensure that a tool remains:

* Available
* Governed
* Correct
* Observable
* Recoverable
* Within its declared cost and latency limits
* Consistent with its contract
* Safe to expose to external graphs
* Capable of generating evidence for future evolution

The maintenance graph surrounds a tool implementation without replacing it.

```text id="yvxiyx"
External graph
      ↓
ServiceFabric tool call
      ↓
Maintenance preflight
      ↓
Tool implementation
      ↓
Maintenance verification and recovery
      ↓
Structured result
```

---

# 2. Maintenance is not unrestricted autonomy

The maintenance graph may direct execution only within the tool’s published contract.

It may:

* Normalize valid arguments
* Check preconditions
* Select among declared providers
* Select among declared implementations
* Use declared fallbacks
* Retry declared transient failures
* Repair provider-specific requests
* Validate outputs
* Verify effects
* Return partial results
* Generate warnings
* Open incidents
* Quarantine unsafe revisions
* Emit evolution proposals

It may not:

* Change the caller’s objective
* Expand caller permissions
* Remove approval requirements
* Introduce undeclared side effects
* Invoke undeclared tools
* Use undeclared models
* Select undeclared providers
* Conceal a failed effect
* Fabricate evidence
* Rewrite the public contract
* Publish a new tool version

The maintenance graph operates under this authority hierarchy:

```text id="xr6cfi"
ServiceFabric invariants
        ↓
Security and governance policy
        ↓
Published ToolRevision
        ↓
Invocation-specific policy decision
        ↓
Maintenance graph decision
        ↓
Implementation execution
```

---

# 3. Stable MCP baseline

As of July 11, 2026, the official MCP site still identifies `2025-11-25` as the latest released specification. ServiceFabric should therefore maintain production conformance to that version while isolating MCP-specific behaviour behind its protocol adapter.

The maintenance runtime should recognize three relevant MCP behaviours:

* Connection capabilities are negotiated during the protocol lifecycle.
* Cancellation is advisory for ordinary requests and should be propagated through the execution stack.
* The `2025-11-25` task mechanism is experimental and should not become ServiceFabric’s canonical persistence model for long-running work.

ServiceFabric should model long-running execution internally and project it into MCP tasks only when:

* The client and server support the feature.
* The tool’s compatibility profile permits it.
* The task semantics can be represented without weakening ServiceFabric governance.

---

# 4. The two maintenance planes

## 4.1 Invocation plane

Runs for every tool invocation.

```text id="9h9v4z"
Call received
   ↓
Resolve revision
   ↓
Verify policy
   ↓
Prepare execution
   ↓
Execute
   ↓
Recover where permitted
   ↓
Validate result
   ↓
Record outcome
   ↓
Return
```

Responsibilities:

* Call-level policy enforcement
* Preconditions
* Provider selection
* Budget enforcement
* Retry and fallback
* Output validation
* Effect verification
* Result classification
* Invocation telemetry

## 4.2 Operational plane

Runs continuously, periodically, or in response to events.

```text id="sp9fsq"
Health signal
   ↓
Assess tool state
   ↓
Diagnose degradation
   ↓
Mitigate
   ↓
Update ToolStatus
   ↓
Incident / quarantine / evolution signal
```

Responsibilities:

* Health checks
* Dependency monitoring
* Provider performance
* Evaluation drift
* Credential expiry
* Contract drift
* Circuit-breaker management
* Incident lifecycle
* Quarantine
* Recovery validation
* Evolution triggers

## 4.3 Separation rule

The invocation plane must not wait for broad operational analysis unless execution safety requires it.

The operational plane must not modify the result of an invocation that has already completed.

They communicate through:

```text id="13g0of"
ToolStatus
ProviderStatus
CircuitState
IncidentRecord
MaintenanceEvent
EvolutionSignal
```

---

# 5. Maintenance resource model

```text id="4sjttb"
ToolRevision
    Immutable desired runtime behaviour

ToolStatus
    Current operational state

ProviderStatus
    Current dependency state

InvocationMaintenanceRecord
    Decisions made during one call

IncidentRecord
    Operational problem requiring tracking

EvolutionSignal
    Evidence that the tool may need redesign
```

## 5.1 `ToolStatus`

```typescript id="iy5fjd"
export interface ToolStatus {
  toolId: string;
  revisionId: string;

  state:
    | "healthy"
    | "degraded"
    | "unavailable"
    | "quarantined"
    | "deprecated";

  readiness: {
    callable: boolean;
    discoverable: boolean;
    reasonCodes: string[];
  };

  health: {
    implementation: HealthComponent;
    dependencies: HealthComponent;
    maintenanceGraph: HealthComponent;
    policies: HealthComponent;
    evaluations: HealthComponent;
  };

  performance: {
    successRate: number;
    partialSuccessRate: number;
    errorRate: number;
    p50LatencyMs: number;
    p95LatencyMs: number;
    p99LatencyMs: number;
  };

  quality: {
    outputValidityRate: number;
    evidenceCoverageRate?: number;
    agentRecoveryRate?: number;
    domainQualityScore?: number;
  };

  activeIncidents: string[];
  circuitState: "closed" | "open" | "half_open";

  lastSuccessfulInvocationAt?: string;
  lastHealthCheckAt?: string;
  lastEvaluationAt?: string;

  updatedAt: string;
}
```

## 5.2 `ProviderStatus`

```typescript id="o9m7p6"
export interface ProviderStatus {
  providerId: string;
  toolId: string;

  state:
    | "healthy"
    | "degraded"
    | "rate_limited"
    | "unavailable"
    | "quarantined";

  capabilities: string[];

  metrics: {
    successRate: number;
    p95LatencyMs: number;
    qualityScore?: number;
    remainingQuota?: number;
    estimatedCostUsd?: number;
  };

  contract: {
    lastVerifiedAt: string;
    schemaHash?: string;
    driftDetected: boolean;
  };

  credentials: {
    state: "valid" | "expiring" | "expired" | "unknown";
    expiresAt?: string;
  };

  updatedAt: string;
}
```

---

# 6. Invocation-maintenance state

```typescript id="sfewjg"
export interface InvocationMaintenanceState<
  TArguments = unknown,
  TData = unknown
> {
  invocation: {
    invocationId: string;
    toolId: string;
    revisionId: string;
    receivedAt: string;
    deadline: string;
    attempt: number;
  };

  caller: {
    principalId: string;
    verified: boolean;
    scopes: string[];
    tenantId?: string;
  };

  arguments: {
    original: TArguments;
    normalized?: TArguments;
    hash: string;
  };

  policy: {
    decisionId: string;
    authorized: boolean;
    approvalRequired: boolean;
    approvalSatisfied: boolean;
    effectClass: string;
  };

  budget: {
    durationRemainingMs: number;
    toolCallsRemaining: number;
    modelCallsRemaining: number;
    tokensRemaining?: number;
    costRemainingUsd?: number;
  };

  execution: {
    plan?: ExecutionPlan;
    attempts: ExecutionAttempt[];
    selectedProvider?: string;
    selectedImplementation?: string;
  };

  result: {
    raw?: unknown;
    normalized?: TData;
    evidence: EvidenceRecord[];
    warnings: ToolWarning[];
    quality?: InvocationQualityAssessment;
  };

  decision?: MaintenanceCompletionDecision;
  events: MaintenanceEvent[];
}
```

---

# 7. Invocation graph topology

```text id="gnm8hv"
M00 START
  ↓
M01 Load tool status and revision
  ↓
M02 Verify invocation eligibility
  ↓
M03 Verify policy decision
  ↓
M04 Validate and normalize arguments
  ↓
M05 Check idempotency and concurrency
  ↓
M06 Establish budgets and deadline
  ↓
M07 Check dependency health
  ↓
M08 Select execution plan
  ↓
M09 Execute attempt
  ├── SUCCESS ──────────────────────→ M14
  ├── PARTIAL_RESPONSE ─────────────→ M13
  └── FAILURE ──────────────────────→ M10
  ↓
M10 Classify failure
  ├── RETRYABLE ────────────────────→ M11
  ├── FALLBACK_AVAILABLE ───────────→ M12
  ├── PARTIAL_RECOVERABLE ──────────→ M13
  ├── UNSAFE ───────────────────────→ M18
  └── TERMINAL ─────────────────────→ M17
  ↓
M11 Retry decision and backoff
  ├── RETRY_ALLOWED ────────────────→ M09
  └── RETRY_EXHAUSTED ──────────────→ M12/M17
  ↓
M12 Select fallback
  ├── FALLBACK_SELECTED ────────────→ M09
  └── NO_FALLBACK ──────────────────→ M13/M17
  ↓
M13 Construct partial result
  ↓
M14 Normalize and validate output
  ↓
M15 Verify evidence and side effects
  ├── VALID ────────────────────────→ M16
  ├── REPAIRABLE ───────────────────→ M10
  ├── UNCERTAIN_EFFECT ─────────────→ M19
  └── UNSAFE ───────────────────────→ M18
  ↓
M16 Classify completion
  ↓
M17 Construct terminal error
  ↓
M18 Quarantine and incident path
  ↓
M19 Effect reconciliation path
  ↓
M20 Record telemetry and update status
  ↓
M21 Emit evolution signals
  ↓
M22 Return canonical ToolResult
  ↓
END
```

---

# 8. M01 — Load revision and status

**Node type:** Deterministic

The graph resolves:

* Exact tool revision
* Active deployment
* Current `ToolStatus`
* Applicable maintenance graph version
* Policy bundle
* Circuit state
* Required provider status
* Current deprecation state

The revision remains fixed for the entire invocation.

Possible outcomes:

```typescript id="dgzc1s"
type InvocationEligibility =
  | { outcome: "eligible" }
  | {
      outcome: "degraded";
      warnings: ToolWarning[];
    }
  | {
      outcome: "unavailable";
      error: ToolError;
    }
  | {
      outcome: "quarantined";
      error: ToolError;
    };
```

A degraded tool may execute only when:

* Its contract permits degraded results.
* Required quality thresholds remain achievable.
* The caller is informed through warnings.
* No safety control is degraded.

---

# 9. M02–M03 — Eligibility and policy

The maintenance graph verifies that:

* The caller identity was authenticated.
* Authorization was evaluated for this exact tool revision.
* Arguments fall within the policy decision’s scope.
* Approval remains valid.
* The declared effect class matches the proposed execution.
* The tool is allowed in the target environment.
* Required data classifications are satisfied.

The graph may consume a policy decision but cannot create an authorization grant itself.

```typescript id="8gd0v6"
export interface InvocationPolicyBinding {
  policyDecisionId: string;
  toolRevisionId: string;
  principalId: string;
  argumentHash?: string;
  approvedEffectClass: string;
  expiresAt: string;
}
```

For state-changing tools, the binding should normally include the argument or action-preview hash.

---

# 10. M04 — Argument normalization

Argument normalization is permitted only when it preserves caller intent.

Permitted examples:

* Trim whitespace.
* Canonicalize case-insensitive identifiers.
* Convert equivalent date representations.
* Resolve a safe declared default.
* Normalize currency codes.
* Remove exact duplicate list items.
* Expand a recognized public identifier into canonical form.

Not permitted:

* Add a new recipient.
* Increase a transaction value.
* Broaden a date range materially.
* Change a repository or account.
* Change a write into a different write.
* Infer approval-sensitive data.
* Substitute a different user.
* Convert an ambiguous instruction into an irreversible action.

```typescript id="jppxi7"
export interface ArgumentNormalizationRecord {
  field: string;
  originalValueHash: string;
  normalizedValueHash: string;
  ruleId: string;
  semanticChange: false;
}
```

Any normalization with a semantic effect must return a validation error or invoke an approved elicitation path rather than proceed silently.

---

# 11. M05 — Idempotency and concurrency

Before execution, the graph checks:

* Existing idempotency record
* Argument hash
* Invocation state
* Required concurrency key
* Existing lock
* Prior effect receipt
* Prior uncertain outcome

Possible decisions:

```typescript id="vhkj6g"
export type IdempotencyDecision =
  | { action: "execute_new" }
  | {
      action: "return_previous";
      resultReference: string;
    }
  | {
      action: "join_in_progress";
      invocationReference: string;
    }
  | {
      action: "reject_conflict";
      error: ToolError;
    }
  | {
      action: "reconcile_uncertain";
      reconciliationReference: string;
    };
```

A state-changing invocation must not be retried until the graph knows whether the earlier attempt committed its effect.

---

# 12. M06 — Budget establishment

Every invocation has explicit limits.

```typescript id="eu410k"
export interface MaintenanceBudget {
  hardDeadline: string;

  maximumAttempts: number;
  maximumProviderCalls: number;
  maximumInternalToolCalls: number;
  maximumModelCalls: number;

  maximumTokens?: number;
  maximumCostUsd?: number;

  maximumResultBytes: number;
  maximumEvidenceRecords: number;
  maximumGraphDepth: number;
}
```

Budgets are derived from:

```text id="xvg18a"
ToolRevision maximum
        ∩
Caller policy maximum
        ∩
Parent graph remaining budget
        ∩
Environment maximum
        ∩
Invocation deadline
```

The maintenance graph may reduce a budget. It may not exceed the most restrictive applicable maximum.

---

# 13. M07 — Dependency health

The graph evaluates required dependencies before selecting an execution plan.

```typescript id="f0ztyr"
export interface DependencyAssessment {
  dependencyId: string;
  required: boolean;

  state:
    | "healthy"
    | "degraded"
    | "unavailable"
    | "unknown";

  observedAt: string;
  freshnessMs: number;

  usable: boolean;
  reasonCodes: string[];
}
```

Health information must be fresh enough for the tool’s risk and latency class.

Examples:

| Tool                        | Acceptable health-cache age |
| --------------------------- | --------------------------: |
| Calculator                  |              Not applicable |
| Web search                  |               30–60 seconds |
| Weather provider            |                 1–5 minutes |
| Market execution            |              Near real time |
| Project task creation       |               30–60 seconds |
| Internal document retrieval |             Several minutes |

A stale health record should not automatically imply failure. The graph may perform a bounded live check where latency permits.

---

# 14. M08 — Execution-plan selection

An execution plan identifies how the tool will be executed without changing its public semantics.

```typescript id="5uvixa"
export interface ExecutionPlan {
  planId: string;

  adapter: ExecutionAdapterType;
  implementationRef: string;
  providerId?: string;

  timeoutMs: number;
  attemptLimit: number;

  requestMappingRef?: string;
  responseMappingRef?: string;

  internalTools: string[];
  modelPurposes: string[];

  expectedEffects: ExpectedEffect[];

  fallbackPlanIds: string[];
  rationaleCodes: string[];
}
```

## 14.1 Selection criteria

The graph may consider:

* Capability support
* Health
* Freshness
* Latency
* Quality
* Cost
* Jurisdiction
* Data classification
* Caller authorization
* Provider quota
* Contract compatibility
* Historical reliability

## 14.2 Deterministic governance

An agent may rank technically acceptable plans, but deterministic controls must first remove plans that violate:

* Data-location policy
* Security policy
* Effect policy
* Provider allowlist
* Cost ceiling
* Tool-call restrictions
* Model-use restrictions

```text id="2u2v5e"
All declared candidates
        ↓
Deterministic policy filtering
        ↓
Operational feasibility filtering
        ↓
Optional agent-assisted ranking
        ↓
Deterministic final validation
        ↓
Selected plan
```

---

# 15. M09 — Execution attempt

```typescript id="w8xlck"
export interface ExecutionAttempt {
  attemptId: string;
  planId: string;
  sequence: number;

  startedAt: string;
  completedAt?: string;

  state:
    | "started"
    | "succeeded"
    | "failed"
    | "cancelled"
    | "timed_out"
    | "uncertain";

  providerRequestId?: string;

  error?: NormalizedDependencyError;
  effectEvidence?: EvidenceRecord[];
}
```

Each attempt must:

* Inherit the invocation trace.
* Receive an abort signal.
* Receive the remaining deadline.
* Receive only declared secrets.
* Receive only permitted internal tools.
* Receive only permitted model access.
* Enforce response-size limits.
* Record cost and resource consumption.

---

# 16. Cancellation

For ordinary MCP requests, cancellation is expressed through a cancellation notification referencing the active request; receivers should stop work where feasible. Task-augmented requests use their task-specific cancellation mechanism.

ServiceFabric should translate external cancellation into:

```text id="q66mry"
External cancellation
        ↓
Invocation CancellationToken
        ↓
Maintenance graph
        ↓
Execution adapter
        ↓
Provider / process / internal graph
```

## 16.1 Cancellation outcomes

```typescript id="0q84vv"
export type CancellationOutcome =
  | "cancelled_before_execution"
  | "cancelled_before_commit"
  | "cancelled_after_commit"
  | "cancellation_not_supported"
  | "effect_state_uncertain";
```

Cancellation must not be reported as successful rollback.

For state-changing tools:

* Cancellation before commit should prevent the effect.
* Cancellation after commit should return the effect receipt.
* Uncertain commit state should enter effect reconciliation.
* Compensation requires a separate declared rollback or compensation operation.

---

# 17. Failure taxonomy

Every failure is normalized before recovery.

```typescript id="x3k0eq"
export type MaintenanceFailureClass =
  | "invalid_input"
  | "authentication_failure"
  | "authorization_failure"
  | "approval_failure"
  | "policy_denial"
  | "dependency_connection"
  | "dependency_timeout"
  | "dependency_rate_limit"
  | "dependency_authentication"
  | "dependency_schema_drift"
  | "dependency_invalid_response"
  | "empty_result"
  | "quality_failure"
  | "evidence_failure"
  | "effect_uncertain"
  | "budget_exhausted"
  | "cancelled"
  | "resource_exhausted"
  | "implementation_defect"
  | "security_violation"
  | "unknown";
```

Each class maps to a default recovery policy.

| Failure class           | Default                             |
| ----------------------- | ----------------------------------- |
| Invalid input           | Return repairable error             |
| Authorization failure   | Return terminal error               |
| Approval failure        | Return approval error               |
| Connection failure      | Retry or fallback                   |
| Timeout                 | Retry only if deadline permits      |
| Rate limit              | Backoff or fallback                 |
| Provider authentication | Do not retry repeatedly             |
| Schema drift            | Quarantine provider                 |
| Invalid output          | Retry/fallback, then fail quality   |
| Evidence failure        | Do not claim success                |
| Effect uncertain        | Reconcile before retry              |
| Security violation      | Stop and incident                   |
| Implementation defect   | Stop, incident, possible quarantine |

---

# 18. M10–M12 — Recovery policy

## 18.1 Recovery decision

```typescript id="k7n91m"
export interface RecoveryDecision {
  action:
    | "retry_same_plan"
    | "retry_repaired_request"
    | "select_fallback"
    | "return_partial"
    | "return_error"
    | "reconcile_effect"
    | "quarantine_provider"
    | "quarantine_tool";

  reasonCodes: string[];

  delayMs?: number;
  nextPlanId?: string;
  repairedRequestHash?: string;

  budgetAfterDecision: MaintenanceBudgetSnapshot;
}
```

## 18.2 Retry eligibility

A retry is permitted only when all are true:

* Failure class is declared retryable.
* Tool is retry-safe.
* Effect has not been committed, or idempotency protects it.
* Attempt budget remains.
* Deadline permits another attempt.
* Cost budget remains.
* Circuit breaker permits execution.
* Provider is not quarantined.
* Retry is unlikely to reproduce a deterministic failure.

## 18.3 Retry anti-patterns

The graph must not:

* Retry authorization denials.
* Retry invalid input unchanged.
* Retry an irreversible operation without idempotency protection.
* Retry after an uncertain financial effect.
* Retry indefinitely.
* Restart a complete agentic workflow for a small downstream error.
* Hide repeated failure behind excessive latency.

## 18.4 Request repair

A provider-specific request may be repaired when:

* The provider rejected a syntactic representation.
* The repair preserves public arguments.
* The mapping rule is declared.
* The new request remains within policy.
* The repair is recorded.

An LLM-based repair may not alter approval-sensitive arguments.

---

# 19. Fallbacks

Fallbacks must be declared in the `ToolRevision`.

```typescript id="4pysnn"
export interface FallbackRule {
  fromPlanId: string;
  toPlanId: string;

  allowedFailureClasses: MaintenanceFailureClass[];

  semanticEquivalence:
    | "equivalent"
    | "degraded_but_compatible";

  additionalWarnings: ToolWarning[];

  maximumUsesPerInvocation: number;
}
```

## 19.1 Equivalent fallback

The alternative is expected to satisfy the same contract.

Example:

```text id="f2dyid"
Primary weather provider
    → secondary weather provider
```

## 19.2 Degraded compatible fallback

The alternative produces less complete but still valid output.

Example:

```text id="wb3ohv"
Real-time market data
    → delayed market data with explicit timestamp and warning
```

The graph must not use a degraded fallback when:

* The caller required real-time execution.
* The contract prohibits stale data.
* The degraded result could cause an unsafe action.
* The missing property is necessary to satisfy success criteria.

---

# 20. Partial results

A partial result is valid only when:

* The output schema permits it.
* Minimum completion criteria are met.
* Missing components are identified.
* Warnings are explicit.
* Evidence covers all returned claims.
* The tool does not represent an unverified write as completed.

```typescript id="w76eh1"
export interface PartialResultAssessment {
  minimumCriteriaSatisfied: boolean;
  completedComponents: string[];
  missingComponents: string[];
  warningCodes: string[];
  safeToReturn: boolean;
}
```

Examples:

| Tool                | Valid partial result                                           |
| ------------------- | -------------------------------------------------------------- |
| Scholarly search    | Two providers succeeded, one failed                            |
| Web search          | Some sources unavailable                                       |
| Portfolio analysis  | Some optional risk metrics unavailable                         |
| Task creation       | Usually no—task either exists or does not                      |
| Email send          | No partial success unless recipients are independently tracked |
| Multi-file analysis | Some files processed, failures enumerated                      |

---

# 21. Output validation

Output validation occurs in layers.

```text id="0n9nqn"
Provider response validation
        ↓
Internal data-model validation
        ↓
Tool output-schema validation
        ↓
Domain-invariant validation
        ↓
Evidence validation
        ↓
Policy and classification validation
```

## 21.1 Output defects

```typescript id="wylyhr"
export type OutputDefect =
  | "schema_violation"
  | "missing_required_data"
  | "invalid_identifier"
  | "impossible_value"
  | "stale_data"
  | "untrusted_content"
  | "insufficient_provenance"
  | "effect_not_verified"
  | "classification_violation"
  | "excessive_size";
```

A provider’s HTTP success does not override a ServiceFabric output defect.

---

# 22. Evidence verification

```typescript id="fn5cdo"
export interface EvidenceVerificationResult {
  valid: boolean;

  coverage: number;
  integrityVerified: boolean;
  sourceTrustScore?: number;

  defects: EvidenceDefect[];

  decision:
    | "accept"
    | "accept_with_warning"
    | "seek_secondary_evidence"
    | "return_partial"
    | "reject_result";
}
```

The graph may seek secondary evidence when:

* A financial value is materially inconsistent.
* A document identifier is malformed.
* A write provider gives no receipt.
* Two providers disagree strongly.
* A source appears stale.
* An external response may contain fabricated citations.
* A security-sensitive assertion requires independent verification.

The graph must not manufacture missing provenance.

---

# 23. Effect verification

For state-changing tools, success requires evidence that the declared effect occurred.

```typescript id="yo464k"
export interface EffectVerification {
  expectedEffect: ExpectedEffect;
  observedState: "committed" | "not_committed" | "uncertain";

  providerReference?: string;
  effectReceipt?: EffectReceipt;

  verifiedAt: string;
  verificationMethod: string;
}
```

## 23.1 Verification examples

| Tool                | Verification                                    |
| ------------------- | ----------------------------------------------- |
| Create task         | Read task by returned identifier                |
| Send email          | Provider message identifier and accepted status |
| Update calendar     | Read event and compare fields                   |
| Modify file         | Read file hash after write                      |
| Create pull request | Retrieve pull request by identifier             |
| Submit payment      | Retrieve transaction state from payment system  |

## 23.2 Uncertain effects

```text id="1kcdpj"
Write request sent
        ↓
Connection lost
        ↓
Commit status unknown
        ↓
Do not retry
        ↓
Enter reconciliation
```

The graph returns an uncertain-effect result only after attempting declared reconciliation.

```typescript id="l1yemr"
export interface UncertainEffectError extends ToolError {
  category: "conflict";
  retryable: false;

  safeDetails: {
    reconciliationId: string;
    target: string;
    providerReference?: string;
  };
}
```

---

# 24. Effect reconciliation

```text id="plmqsi"
Uncertain effect
      ↓
Search by idempotency key
      ↓
Search by provider reference
      ↓
Read target state
      ↓
Compare expected mutation
      ├── COMMITTED ─────────→ return success receipt
      ├── NOT_COMMITTED ─────→ permit controlled retry
      └── STILL_UNCERTAIN ───→ incident and human escalation
```

Reconciliation may run:

* Within the original invocation
* As a short internal task
* Through a human-task adapter
* Through the operational maintenance plane

It must retain the original:

* Revision
* Arguments hash
* Approval binding
* Idempotency key
* Provider
* Expected effect

---

# 25. Agentic maintenance

Some maintenance decisions benefit from model assistance, especially for:

* Query normalization
* Semantic result ranking
* Classification of provider text errors
* Detection of contradictory research results
* Structured extraction
* Diagnosis of software failures
* Determination of whether partial results answer the bounded request

Model use must remain constrained.

```typescript id="5uw4s3"
export interface MaintenanceModelRequest {
  purpose: string;

  inputReference: string;
  outputSchema: object;

  permittedDataClassification: string;
  maximumTokens: number;
  maximumCostUsd: number;

  prohibitedDecisions: string[];
}
```

## 25.1 Model-prohibited maintenance decisions

A model must not be the sole decision-maker for:

* Authorization
* Approval validity
* Secret selection
* Provider trust
* Financial-limit enforcement
* Whether an effect committed
* Whether to suppress an incident
* Whether to quarantine a security violation
* Whether evidence exists
* Whether to exceed a budget

## 25.2 Model failure handling

If model assistance fails:

* The deterministic fallback should be used where possible.
* The tool may return a less-ranked but valid result.
* Agentic enhancement may be skipped.
* A model failure must not convert invalid output into valid output.

---

# 26. Circuit breaker

```typescript id="l65ljr"
export interface CircuitBreakerState {
  key: string;
  state: "closed" | "open" | "half_open";

  failureCount: number;
  successCount: number;

  openedAt?: string;
  nextProbeAt?: string;

  reasonCodes: string[];
}
```

## 26.1 Circuit scope

Circuits may be keyed by:

* Tool revision
* Provider
* Provider operation
* Tenant-provider pair
* Model provider
* Database dependency
* External MCP server

## 26.2 Opening conditions

Examples:

* Repeated dependency timeout
* High invalid-response rate
* Authentication failure
* Schema drift
* Excessive rate limiting
* Quality collapse
* Security violation

## 26.3 Half-open probes

A half-open probe should:

* Use a safe read-only request where possible.
* Avoid real side effects.
* Be rate limited.
* Validate both connectivity and contract.
* Close the circuit only after sufficient successful probes.

---

# 27. Operational health graph

```text id="vgpqss"
O00 Trigger
  ├── scheduled
  ├── invocation signal
  ├── provider event
  ├── security event
  ├── evaluation failure
  └── manual request
  ↓
O01 Load operational state
  ↓
O02 Validate health signals
  ↓
O03 Assess tool health
  ↓
O04 Assess dependency health
  ↓
O05 Assess quality and drift
  ↓
O06 Determine operational state
  ├── HEALTHY ────────────────────→ O11
  ├── DEGRADED ───────────────────→ O07
  ├── UNAVAILABLE ────────────────→ O08
  ├── UNSAFE ─────────────────────→ O09
  └── EVOLUTION_NEEDED ───────────→ O10
  ↓
O07 Apply degradation controls
  ↓
O08 Open incident and disable calls
  ↓
O09 Quarantine revision or provider
  ↓
O10 Emit evolution signal
  ↓
O11 Update ToolStatus
  ↓
O12 Notify affected systems
  ↓
END
```

---

# 28. Operational triggers

```typescript id="im74sa"
export type OperationalMaintenanceTrigger =
  | {
      type: "scheduled_health_check";
      scheduledAt: string;
    }
  | {
      type: "invocation_threshold_breach";
      metric: string;
      observedValue: number;
    }
  | {
      type: "dependency_event";
      providerId: string;
      eventCode: string;
    }
  | {
      type: "security_event";
      incidentReference: string;
    }
  | {
      type: "evaluation_failure";
      evaluationReference: string;
    }
  | {
      type: "contract_drift";
      dependencyId: string;
      previousHash: string;
      currentHash: string;
    }
  | {
      type: "manual";
      requestedBy: string;
      reason: string;
    };
```

---

# 29. Health checks

Health checks should distinguish:

```text id="97swb6"
Liveness
    Is the process functioning?

Readiness
    Can it satisfy the tool contract now?

Dependency health
    Are required systems usable?

Quality health
    Are outputs still correct enough?

Policy health
    Can required security controls be enforced?
```

## 29.1 Health-check examples

### Calculator

* Parser loads.
* Known expressions evaluate correctly.
* Complexity limits work.
* No network access is present.

### Research search

* At least one permitted provider is available.
* Provider schemas remain compatible.
* DOI validation works.
* Provenance coverage remains above threshold.

### Task creation

* Authentication is valid.
* Provider is reachable.
* Create and read permissions exist.
* Idempotency storage is available.
* Effect verification works.

### Code runner

* Sandbox launches.
* Filesystem isolation works.
* Network restrictions work.
* Resource limits are enforced.
* Malicious probe cannot escape.

---

# 30. Drift detection

The maintenance graph monitors several forms of drift.

```typescript id="c7imk4"
export type DriftType =
  | "provider_schema"
  | "provider_semantics"
  | "authentication"
  | "tool_selection"
  | "argument_patterns"
  | "output_quality"
  | "latency"
  | "cost"
  | "security"
  | "dependency_version"
  | "model_behavior"
  | "user_expectation";
```

## 30.1 Contract drift

Detected when:

* Provider schema hash changes.
* Required field disappears.
* Enumeration changes.
* Error format changes.
* Tool inventory changes on a federated MCP server.
* Output meaning changes despite schema compatibility.

## 30.2 Agent-callability drift

Detected when:

* Invalid-call rate rises.
* Agents confuse this tool with another.
* Callers repeatedly omit the same field.
* Callers misuse partial results.
* Agents retry terminal errors.
* Callers avoid a tool that should be selected.

## 30.3 Quality drift

Detected when:

* Evidence coverage falls.
* Provider agreement falls.
* Benchmark performance declines.
* Hallucinated or unsupported data appears.
* Model ranking becomes less relevant.
* Financial calculations differ from reference implementations.

---

# 31. Incident management

```typescript id="vtnj5p"
export interface IncidentRecord {
  incidentId: string;

  toolId: string;
  revisionId?: string;
  providerId?: string;

  severity:
    | "low"
    | "medium"
    | "high"
    | "critical";

  category:
    | "availability"
    | "quality"
    | "security"
    | "data"
    | "cost"
    | "performance"
    | "contract"
    | "effect";

  status:
    | "open"
    | "investigating"
    | "mitigated"
    | "resolved"
    | "closed";

  summary: string;
  evidenceRefs: string[];

  detectedAt: string;
  mitigatedAt?: string;
  resolvedAt?: string;

  automaticActions: string[];
  assignedOwners: string[];

  evolutionSignalId?: string;
}
```

## 31.1 Incident creation conditions

Create an incident when:

* Tool enters unavailable state.
* Security violation occurs.
* Effect remains uncertain.
* Output validity breaches a critical threshold.
* Evidence fabrication is detected.
* Provider contract changes unexpectedly.
* Financial or external communication effect differs from request.
* Quarantine occurs.
* Error rate remains above threshold.
* Cost amplification is detected.

Routine transient failures should be recorded as invocation events, not necessarily incidents.

---

# 32. Quarantine

Quarantine prevents a tool or provider from continuing unsafe or misleading operation.

## 32.1 Quarantine scopes

```typescript id="hmy49t"
export type QuarantineScope =
  | "tool_revision"
  | "deployment"
  | "provider"
  | "provider_operation"
  | "maintenance_graph"
  | "model_configuration";
```

## 32.2 Automatic quarantine triggers

* Unauthorized side effect
* Fabricated effect receipt
* Repeated output-schema violation
* Critical security control failure
* Secret leakage
* Cross-tenant data exposure
* Provider identity mismatch
* Undeclared network destination
* Undeclared tool or model invocation
* Confirmed evidence fabrication
* Sandbox escape
* Tool behaviour inconsistent with effect declaration

## 32.3 Quarantine action

```text id="98p04d"
Trigger confirmed
      ↓
Stop new invocations
      ↓
Cancel safe in-progress work
      ↓
Preserve audit evidence
      ↓
Update ToolStatus
      ↓
Remove or mark tool in discovery
      ↓
Open incident
      ↓
Notify owners
      ↓
Require recovery verification
```

## 32.4 Discovery behaviour

Two valid policies exist:

### Hidden quarantine

The tool is removed from discovery.

Use when:

* Exposure itself is unsafe.
* A replacement exists.
* Callers should not plan around the capability.

### Visible unavailable

The tool remains discoverable but rejects calls.

Use when:

* Callers need to know the capability is temporarily unavailable.
* External graphs can select a different strategy.
* The tool contract remains valid but the implementation is offline.

---

# 33. Recovery from quarantine

A quarantined component cannot return to service solely because time passed.

Required recovery evidence may include:

* Defect resolution
* New immutable revision
* Security review
* Contract tests
* Regression tests
* Provider identity verification
* Health probes
* Agent-callability evaluation
* Canary execution
* Human approval

```typescript id="pt6f1r"
export interface QuarantineReleaseDecision {
  scope: QuarantineScope;
  targetId: string;

  evidenceRefs: string[];

  decision:
    | "remain_quarantined"
    | "release_to_canary"
    | "release_to_active";

  approvedBy: string[];
  decidedAt: string;
}
```

A materially changed tool implementation should normally be released as a new revision through the system-evolution graph rather than mutating the quarantined revision.

---

# 34. Degradation controls

A degraded tool may remain callable with restrictions.

Possible controls:

* Disable a failing provider.
* Reduce maximum result count.
* Disable optional model ranking.
* Use cached data with explicit age.
* Limit tool availability to lower-risk calls.
* Disable write operations while preserving reads.
* Require human approval temporarily.
* Increase warnings.
* Reduce concurrency.
* Tighten cost limits.
* Route to a stable prior revision.

```typescript id="7m4pye"
export interface DegradationPolicy {
  reasonCode: string;

  disabledFeatures: string[];
  restrictedEffects: string[];

  maximumResultAge?: string;
  maximumConcurrency?: number;

  forcedWarnings: ToolWarning[];

  expiresAt?: string;
}
```

Degradation must not silently weaken contract guarantees.

---

# 35. Rollback

Rollback applies to deployments and configurations, not immutable revisions.

```text id="qyu743"
Active revision N
      ↓ incident
Prior known-good revision N-1
      ↓ compatibility check
Policy and schema compatibility
      ↓ canary
Traffic shift
```

Rollback is permitted when:

* Caller-facing contract remains compatible.
* Required policies still apply.
* The prior revision is not vulnerable.
* Data migrations are compatible.
* Effect semantics have not changed incompatibly.

A rollback that changes public semantics requires explicit registry and caller handling rather than transparent traffic switching.

---

# 36. Maintenance telemetry

## 36.1 Invocation metrics

```text id="bjli73"
maintenance_invocations_total
maintenance_preflight_failures_total
maintenance_retries_total
maintenance_fallbacks_total
maintenance_partial_results_total
maintenance_effect_reconciliations_total
maintenance_evidence_failures_total
maintenance_budget_exhaustions_total
maintenance_cancellations_total
maintenance_quarantine_events_total
```

## 36.2 Operational metrics

```text id="3tnf7m"
tool_health_state
tool_readiness_state
tool_circuit_state
provider_health_state
provider_contract_drift_total
tool_incidents_open
tool_quality_score
tool_schema_validity_rate
tool_evidence_coverage_rate
tool_agent_recovery_rate
tool_cost_per_success
tool_fallback_success_rate
```

## 36.3 Trace structure

```text id="n27pdd"
tool.maintenance
├── revision.load
├── eligibility.check
├── policy.verify
├── arguments.normalize
├── idempotency.check
├── budget.establish
├── dependencies.assess
├── plan.select
├── attempt.execute
│   ├── provider.call
│   ├── model.call
│   └── internal_tool.call
├── failure.classify
├── recovery.decide
├── output.validate
├── evidence.verify
├── effect.verify
├── completion.classify
├── status.update
└── evolution.evaluate
```

---

# 37. Privacy and retention

The maintenance graph should retain decisions and evidence without unnecessarily retaining sensitive content.

```typescript id="jke57i"
export interface MaintenanceRetentionPolicy {
  arguments:
    | "none"
    | "hash_only"
    | "redacted"
    | "encrypted_full";

  results:
    | "none"
    | "metadata_only"
    | "redacted"
    | "encrypted_full";

  evidenceRetention: string;
  auditRetention: string;
  incidentRetention: string;
}
```

Default principles:

* Retain argument hashes for idempotency and audit.
* Retain full content only when necessary and permitted.
* Never log secrets.
* Redact personal and confidential data.
* Separate operational logs from evidence stores.
* Apply tenant-specific encryption and access.
* Avoid sending sensitive provider payloads to models.

---

# 38. MCP security boundary

For HTTP authorization, MCP requires servers to validate that inbound tokens are intended for that server and prohibits passing the client token unchanged to downstream APIs. ServiceFabric must therefore maintain separate credentials for upstream providers or use provider-specific delegated authorization.

The maintenance graph must also treat MCP session identifiers as correlation mechanisms, not authentication. Official security guidance requires inbound authorization checks and warns against using sessions as authentication.

```text id="ai527o"
MCP client credential
        ↓
Validate for ServiceFabric
        ↓
ServiceFabric authorization
        ↓
Provider-specific credential resolution
        ↓
Downstream call
```

---

# 39. External MCP maintenance

Federated MCP tools require additional supervision.

```text id="en1sl9"
ServiceFabric public tool
        ↓
Federated MCP maintenance
        ↓
External MCP server
```

Maintenance responsibilities:

* Verify server identity.
* Verify supported protocol profile.
* Refresh tool inventory.
* Compare tool schema hashes.
* Normalize tool names.
* Validate annotations independently.
* Filter unsafe or unsupported tools.
* Revalidate every output.
* Isolate external credentials.
* Monitor tool-list drift.
* Apply ServiceFabric errors.
* Quarantine individual external tools where possible.

External MCP annotations are informative. They do not replace ServiceFabric effect classification or authorization.

---

# 40. Long-running operations

ServiceFabric should represent long-running work through its own canonical resource.

```typescript id="e243h6"
export interface ServiceFabricOperation {
  operationId: string;

  toolId: string;
  revisionId: string;

  state:
    | "accepted"
    | "running"
    | "awaiting_input"
    | "awaiting_approval"
    | "succeeded"
    | "failed"
    | "cancelled"
    | "uncertain";

  progress?: OperationProgress;

  resultRef?: string;
  error?: ToolError;

  createdAt: string;
  updatedAt: string;
  expiresAt?: string;
}
```

MCP tasks may be used as a protocol projection where compatible, but the released `2025-11-25` task feature is explicitly experimental.

```text id="s3j6lt"
ServiceFabricOperation
        ├── MCP task projection
        ├── REST operation projection
        ├── internal graph handle
        └── user-interface job
```

---

# 41. Maintenance-to-evolution feedback

Maintenance should not redesign the tool directly. It emits structured evidence.

```typescript id="7ccf3z"
export interface EvolutionSignal {
  signalId: string;

  toolId: string;
  revisionId: string;

  type:
    | "repeated_invalid_calls"
    | "selection_confusion"
    | "provider_drift"
    | "quality_decline"
    | "latency_regression"
    | "cost_regression"
    | "security_defect"
    | "missing_capability"
    | "recurring_fallback"
    | "recurring_composition"
    | "maintenance_complexity"
    | "manual_request";

  severity: "low" | "medium" | "high" | "critical";

  evidenceRefs: string[];
  observedWindow: {
    from: string;
    to: string;
  };

  suggestedArea:
    | "description"
    | "schema"
    | "implementation"
    | "provider"
    | "maintenance_graph"
    | "policy"
    | "tool_boundary"
    | "new_tool";

  createdAt: string;
}
```

## 41.1 Evolution-trigger examples

| Observation                                 | Possible evolution                 |
| ------------------------------------------- | ---------------------------------- |
| Agents repeatedly omit one field            | Improve schema or default          |
| Search fallback used on most calls          | Promote fallback or change routing |
| Same three tools always called together     | Consider composite tool            |
| Maintenance graph requires too many repairs | Redesign implementation            |
| Provider output schema changes              | Update adapter revision            |
| Cost rises materially                       | Change provider or algorithm       |
| Tool confused with another                  | Improve descriptions or boundaries |
| Partial results no longer satisfy callers   | Expand or split capability         |
| Security incident                           | New revision and control changes   |

---

# 42. Maintenance decision records

```typescript id="b8xl19"
export interface MaintenanceDecisionRecord {
  decisionId: string;
  invocationId?: string;
  operationalRunId?: string;

  decisionType:
    | "provider_selection"
    | "retry"
    | "fallback"
    | "partial_result"
    | "effect_reconciliation"
    | "degradation"
    | "incident"
    | "quarantine"
    | "evolution_signal";

  selectedAction: string;
  reasonCodes: string[];

  consideredAlternatives: string[];

  evidenceRefs: string[];

  decisionMaker:
    | "deterministic_rule"
    | "policy_engine"
    | "maintenance_agent"
    | "human_operator";

  createdAt: string;
}
```

The record should capture the conclusion and evidence, not private model reasoning.

---

# 43. Maintenance graph node interface

```typescript id="m5oz7c"
export interface MaintenanceGraphNode<
  TInput = InvocationMaintenanceState,
  TOutput = Partial<InvocationMaintenanceState>
> {
  id: string;
  version: string;

  type:
    | "deterministic"
    | "analysis_agent"
    | "execution"
    | "policy"
    | "transaction"
    | "human_gate";

  execute(
    state: TInput,
    context: MaintenanceNodeContext
  ): Promise<MaintenanceNodeResult<TOutput>>;
}
```

```typescript id="1ox2go"
export interface MaintenanceNodeContext {
  invocationId?: string;
  operationalRunId?: string;

  signal: AbortSignal;
  deadline: Date;

  registry: ToolRegistryClient;
  status: ToolStatusStore;
  providers: ProviderStatusStore;

  policies: MaintenancePolicyClient;
  approvals: ApprovalService;

  adapters: ExecutionAdapterRegistry;
  tools: RestrictedToolClient;
  models: RestrictedModelClient;

  incidents: IncidentService;
  evolution: EvolutionSignalService;

  telemetry: TelemetryService;
  audit: AuditRecorder;
  budget: MaintenanceBudgetController;
}
```

---

# 44. Declarative invocation graph

```yaml id="cxj3b9"
apiVersion: servicefabric.ai/v1alpha1
kind: SystemMaintenanceGraph

metadata:
  id: standard-tool-maintenance
  version: 1.0.0
  owner: servicefabric-platform

spec:
  mode: per_invocation
  entryNode: load-state

  nodes:
    load-state:
      type: deterministic
      handler: maintenance.load-state
      next: eligibility

    eligibility:
      type: deterministic
      handler: maintenance.check-eligibility
      routes:
        eligible: policy
        degraded: policy
        unavailable: terminal-error
        quarantined: terminal-error

    policy:
      type: policy
      handler: maintenance.verify-policy
      routes:
        allowed: normalize-input
        denied: terminal-error
        approval_required: approval-check

    approval-check:
      type: deterministic
      handler: maintenance.verify-approval
      routes:
        approved: normalize-input
        missing: terminal-error
        invalid: terminal-error

    normalize-input:
      type: deterministic
      handler: maintenance.normalize-input
      routes:
        valid: idempotency
        repairable_error: terminal-error
        semantic_ambiguity: terminal-error

    idempotency:
      type: transaction
      handler: maintenance.check-idempotency
      routes:
        execute_new: budget
        return_previous: validate-output
        join_in_progress: return-operation
        conflict: terminal-error
        reconcile: effect-reconciliation

    budget:
      type: deterministic
      handler: maintenance.establish-budget
      next: dependency-health

    dependency-health:
      type: deterministic
      handler: maintenance.assess-dependencies
      routes:
        usable: plan
        degraded: plan
        unavailable: failure-classification

    plan:
      type: deterministic
      handler: maintenance.select-plan
      next: execute

    execute:
      type: execution
      handler: maintenance.execute-plan
      routes:
        success: validate-output
        partial: partial-result
        failure: failure-classification
        uncertain_effect: effect-reconciliation

    failure-classification:
      type: deterministic
      handler: maintenance.classify-failure
      routes:
        retry: retry
        fallback: fallback
        partial: partial-result
        terminal: terminal-error
        unsafe: quarantine
        reconcile: effect-reconciliation

    retry:
      type: deterministic
      handler: maintenance.decide-retry
      routes:
        allowed: execute
        exhausted_with_fallback: fallback
        exhausted_partial: partial-result
        exhausted_terminal: terminal-error

    fallback:
      type: deterministic
      handler: maintenance.select-fallback
      routes:
        selected: execute
        none_partial: partial-result
        none_terminal: terminal-error

    partial-result:
      type: deterministic
      handler: maintenance.construct-partial
      routes:
        valid: validate-output
        invalid: terminal-error

    validate-output:
      type: deterministic
      handler: maintenance.validate-output
      routes:
        valid: verify-evidence
        repairable: failure-classification
        invalid: terminal-error
        unsafe: quarantine

    verify-evidence:
      type: deterministic
      handler: maintenance.verify-evidence
      routes:
        valid: verify-effects
        warning: verify-effects
        seek_secondary: secondary-verification
        invalid: terminal-error

    secondary-verification:
      type: execution
      handler: maintenance.obtain-secondary-evidence
      routes:
        verified: verify-effects
        partial: partial-result
        failed: terminal-error

    verify-effects:
      type: deterministic
      handler: maintenance.verify-effects
      routes:
        no_effect: classify-completion
        committed: classify-completion
        not_committed: terminal-error
        uncertain: effect-reconciliation

    effect-reconciliation:
      type: execution
      handler: maintenance.reconcile-effect
      routes:
        committed: classify-completion
        not_committed_retryable: retry
        not_committed_terminal: terminal-error
        uncertain: incident

    classify-completion:
      type: deterministic
      handler: maintenance.classify-completion
      next: record

    terminal-error:
      type: deterministic
      handler: maintenance.construct-error
      next: record

    quarantine:
      type: transaction
      handler: maintenance.quarantine
      next: incident

    incident:
      type: transaction
      handler: maintenance.open-incident
      next: record

    record:
      type: transaction
      handler: maintenance.record-outcome
      next: evolution-signals

    evolution-signals:
      type: deterministic
      handler: maintenance.evaluate-evolution-signals
      next: return-result

    return-result:
      type: deterministic
      handler: maintenance.return-result
```

---

# 45. Declarative operational graph

```yaml id="lpwtz1"
apiVersion: servicefabric.ai/v1alpha1
kind: SystemMaintenanceGraph

metadata:
  id: standard-tool-operations
  version: 1.0.0
  owner: servicefabric-platform

spec:
  mode: operational
  entryNode: load-operational-state

  triggers:
    - scheduled
    - invocation_threshold
    - dependency_event
    - security_event
    - evaluation_failure
    - contract_drift
    - manual

  nodes:
    load-operational-state:
      type: deterministic
      handler: operations.load-state
      next: validate-signals

    validate-signals:
      type: deterministic
      handler: operations.validate-signals
      next: assess-health

    assess-health:
      type: deterministic
      handler: operations.assess-tool-health
      next: assess-dependencies

    assess-dependencies:
      type: deterministic
      handler: operations.assess-dependencies
      next: assess-quality

    assess-quality:
      type: deterministic
      handler: operations.assess-quality
      next: determine-state

    determine-state:
      type: deterministic
      handler: operations.determine-state
      routes:
        healthy: update-status
        degraded: apply-degradation
        unavailable: disable-and-incident
        unsafe: quarantine
        evolution_needed: emit-evolution

    apply-degradation:
      type: transaction
      handler: operations.apply-degradation
      next: update-status

    disable-and-incident:
      type: transaction
      handler: operations.disable-tool
      next: open-incident

    quarantine:
      type: transaction
      handler: operations.quarantine
      next: open-incident

    open-incident:
      type: transaction
      handler: operations.open-incident
      next: emit-evolution

    emit-evolution:
      type: transaction
      handler: operations.emit-evolution-signal
      next: update-status

    update-status:
      type: transaction
      handler: operations.update-tool-status
      next: notify

    notify:
      type: execution
      handler: operations.notify-affected-systems
```

---

# 46. Reference maintenance flow: `math.calculate`

```text id="3xwptu"
1. Resolve active calculator revision.
2. Confirm tool is healthy.
3. Verify caller scope.
4. Validate expression length and syntax.
5. Establish two-second deadline.
6. Confirm no external dependencies.
7. Select native-function execution plan.
8. Evaluate through safe parser.
9. Validate numeric result.
10. Record calculation trace where configured.
11. Return success.

Failure handling:
- Syntax error → repairable validation error.
- Complexity limit → terminal resource error.
- Runtime defect → incident and possible quarantine.
- No retries against deterministic invalid input.
```

The maintenance graph is guarded but not model-backed.

---

# 47. Reference maintenance flow: `research.search_papers`

```text id="d0ezhr"
1. Resolve revision and current provider status.
2. Verify research.read authorization.
3. Normalize the query without changing meaning.
4. Establish:
     - 20-second deadline
     - 3 provider attempts
     - 2 model calls
     - $0.10 maximum cost
5. Filter providers by:
     - health
     - date-filter support
     - data policy
     - quota
6. Select two providers.
7. Execute searches concurrently within limits.
8. One provider returns malformed metadata.
9. Classify as invalid provider response.
10. Exclude malformed records.
11. Use declared fallback if deadline permits.
12. Merge and deduplicate valid records.
13. Validate DOI and arXiv identifiers.
14. Use model assistance only for relevance ranking.
15. Require provenance for every returned record.
16. Classify:
     - success when coverage requirements are met
     - partial when one provider failed but useful results remain
17. Update provider quality and schema-drift metrics.
18. Emit evolution signal if malformed responses recur.
```

---

# 48. Reference maintenance flow: `project.create_task`

```text id="vrxzlg"
1. Resolve revision and task-provider status.
2. Verify caller and project scope.
3. Verify action-preview approval.
4. Verify approval hash matches arguments.
5. Reserve idempotency key.
6. Acquire project concurrency lock where required.
7. Create task.
8. Connection drops after request transmission.
9. Mark effect state uncertain.
10. Do not retry immediately.
11. Reconcile using:
      - idempotency key
      - provider request identifier
      - task search
12. If task exists:
      - verify its fields
      - return effect receipt
13. If task does not exist:
      - retry only if approval and deadline remain valid
14. If state remains uncertain:
      - open incident
      - return non-retryable uncertainty error
```

---

# 49. Reference maintenance flow: federated MCP tool

```text id="quyw3f"
1. Resolve ServiceFabric wrapper revision.
2. Verify external MCP server identity and health.
3. Confirm cached external tool schema still matches.
4. Apply ServiceFabric authorization.
5. Validate caller arguments against ServiceFabric schema.
6. Map arguments to external MCP contract.
7. Call external MCP server.
8. Validate returned protocol message.
9. Validate structured output independently.
10. Normalize external error.
11. Strip unsafe provider metadata.
12. Attach ServiceFabric provenance.
13. Record external server latency and quality.
14. Quarantine external tool if schema or effect drift is detected.
```

---

# 50. Maintenance testing

Every maintenance graph requires:

## 50.1 Route tests

* Every route is reachable where intended.
* Every route terminates.
* No unbounded retry or fallback loop exists.
* Quarantine routes cannot return success.
* Effect uncertainty cannot bypass reconciliation.

## 50.2 Policy tests

* Unauthorized caller
* Missing approval
* Expired approval
* Modified arguments
* Cross-tenant invocation
* Disallowed provider
* Disallowed model
* Excessive budget request

## 50.3 Recovery tests

* Connection failure
* Timeout
* Rate limit
* Invalid response
* Empty response
* Provider degradation
* Fallback success
* Fallback failure
* Partial result
* Retry exhaustion

## 50.4 Effect tests

* Effect committed
* Effect rejected
* Connection lost before commit
* Connection lost after commit
* Duplicate invocation
* Argument mismatch under reused idempotency key
* Failed effect verification
* Compensation operation

## 50.5 Security tests

* Prompt injection
* Secret request
* Undeclared tool invocation
* Undeclared model call
* Token passthrough
* SSRF
* Schema poisoning
* Forged evidence
* Forged effect receipt
* Recursive call amplification

## 50.6 Operational tests

* Circuit opens.
* Half-open probe succeeds.
* Half-open probe fails.
* Provider quarantine.
* Tool quarantine.
* Recovery to canary.
* Status propagation.
* Evolution signal generation.

---

# 51. Maintenance service-level objectives

Example maintenance SLOs:

```yaml id="3t4g0w"
policyVerificationP95Ms: 50
maintenanceOverheadP95Ms: 150
statusFreshnessSeconds: 60
criticalIncidentDetectionSeconds: 30
quarantinePropagationSeconds: 15
outputValidationRate: 1.0
effectVerificationRate: 1.0
auditRecordRate: 1.0
```

Maintenance overhead should exclude the underlying provider execution time.

High-risk tools may accept higher maintenance latency in exchange for stronger verification.

---

# 52. System-maintenance invariants

```text id="vnxzfz"
SF-M001  Every invocation uses an immutable ToolRevision.
SF-M002  Every invocation begins with a verified policy binding.
SF-M003  Maintenance cannot expand caller authorization.
SF-M004  Maintenance cannot remove an approval requirement.
SF-M005  Every invocation has a hard deadline.
SF-M006  Every retry is bounded.
SF-M007  Every fallback is declared in the ToolRevision.
SF-M008  Every model call has a declared purpose and budget.
SF-M009  Every internal tool call is allowlisted.
SF-M010  Every provider is policy-approved before selection.
SF-M011  Every output is validated before return.
SF-M012  Every external-data result follows provenance policy.
SF-M013  Every write success has an effect receipt.
SF-M014  An uncertain write is not retried before reconciliation.
SF-M015  Cancellation is not represented as rollback.
SF-M016  Partial results must satisfy minimum completion criteria.
SF-M017  Degraded operation must be disclosed.
SF-M018  Tool errors use stable ServiceFabric error codes.
SF-M019  Protocol errors remain distinct from tool errors.
SF-M020  External content cannot modify maintenance policy.
SF-M021  Client credentials are not passed through to providers.
SF-M022  Sessions are not used as authentication.
SF-M023  Every maintenance decision records reason codes.
SF-M024  Every invocation updates operational telemetry.
SF-M025  Every critical security violation opens an incident.
SF-M026  Unsafe behaviour triggers quarantine.
SF-M027  Quarantine cannot expire without verification.
SF-M028  Published revisions are never modified in place.
SF-M029  Design changes are routed to the evolution graph.
SF-M030  Maintenance agents cannot publish revisions.
SF-M031  Retry and fallback loops have explicit maximums.
SF-M032  Every effect uncertainty remains traceable.
SF-M033  Tool status is separate from the authored definition.
SF-M034  Operational state cannot silently weaken the contract.
SF-M035  Long-running state uses explicit operation identifiers.
```

---

# 53. Architectural decision

ServiceFabric should define the maintenance system through four stable boundaries:

```text id="9wjygf"
InvocationMaintenanceGraph
    Supports an individual call

OperationalMaintenanceGraph
    Maintains tool readiness and health

ToolStatus and IncidentRecord
    Represent observed state

EvolutionSignal
    Transfers redesign needs to system evolution
```

The full lifecycle becomes:

```text id="k068ph"
System-Building Graph
        ↓
Immutable ToolRevision
        ↓
System-Maintenance Graph
        ├── supports calls
        ├── verifies outputs and effects
        ├── manages health
        ├── handles incidents
        └── produces evolution evidence
                    ↓
System-Evolution Graph
        ↓
New ToolDefinition and revision
```

The maintenance graph therefore serves as the tool’s **bounded operational intelligence**.

It gives external agent graphs a stable capability while hiding provider selection, recovery, verification, incident handling, and operational complexity behind a governed contract.
