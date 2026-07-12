# ServiceFabric Telemetry, Evaluation, and Agent-Callability Testing Framework v1

**Status:** Architecture baseline
**Subsystem:** Observability and quality control plane
**API version:** `servicefabric.ai/v1alpha1`
**MCP production profile:** `2025-11-25`
**Primary objective:** Determine whether tools and graphs are operationally healthy, semantically correct, safely callable, economically efficient, and useful to agentic systems.

---

# 1. Purpose

The ServiceFabric telemetry and evaluation framework measures five distinct questions:

```text id="84noyg"
1. Did the system execute?
2. Did it execute according to its contract?
3. Did the agent choose and call the right tool?
4. Did the result help complete the intended objective?
5. Did execution remain safe, authorized and efficient?
```

Traditional application monitoring often concentrates on availability, latency and errors. ServiceFabric also requires measurements of:

* Tool-selection quality
* Argument-construction quality
* Result interpretation
* Evidence sufficiency
* Graph completion
* Side-effect correctness
* Agent recovery
* Model and provider variability
* Security-policy enforcement
* Cost and token consumption
* Tool and graph evolution outcomes

The framework produces evidence for:

```text id="ukmrcx"
System-Building Graph
    Publication and quality gates

System-Maintenance Graph
    Health, degradation, incidents and quarantine

System-Evolution Graph
    Root-cause evidence, experiments and promotion

Tool Registry
    Quality-aware discovery and routing

Governance Framework
    Authorization, approval and effect audits
```

---

# 2. Standards alignment

ServiceFabric should use **OpenTelemetry** as its vendor-neutral telemetry foundation.

OpenTelemetry defines common observability signals—including traces, metrics, logs and baggage—and shared semantic conventions intended to provide consistent naming across codebases and platforms. Its context-propagation model allows causally related telemetry to be correlated across services and process boundaries.

ServiceFabric should extend—not replace—OpenTelemetry conventions with a dedicated semantic namespace for:

* Agent graphs
* Tool discovery
* Tool selection
* Tool invocation
* Maintenance decisions
* Model calls
* Approval
* Side effects
* Evaluations
* Evolution experiments

The framework also follows the NIST AI Risk Management Framework principle that AI risk work must include governance, mapping, measurement and management rather than relying only on pre-deployment testing.

For MCP-facing tools, evaluation must distinguish protocol failures from tool-execution failures. Under MCP `2025-11-25`, malformed protocol requests and unknown tools are protocol errors, while API, validation and business-logic failures are normally represented in the tool result with `isError: true`.

---

# 3. Core observability model

ServiceFabric should treat observability as five coordinated signal families.

```text id="v7ih1h"
Traces
    What execution path occurred?

Metrics
    How often and how well does it occur?

Logs and events
    What discrete condition or decision occurred?

Profiles
    Where are runtime resources consumed?

Evaluation records
    Was behaviour semantically correct and useful?
```

OpenTelemetry should carry the first four families where supported. ServiceFabric evaluation resources should carry the fifth while linking back to the same trace and artifact identities.

## 3.1 Traces

Used to reconstruct:

* Graph execution
* Tool discovery
* Tool selection
* Policy decisions
* Tool calls
* Provider calls
* Model calls
* Retry and fallback
* Side-effect verification
* Evaluation execution
* Deployment experiments

## 3.2 Metrics

Used to monitor:

* Availability
* Latency
* Error rates
* Selection accuracy
* Argument validity
* Evidence coverage
* Cost
* Token consumption
* Side-effect reliability
* Agent completion
* Evolution improvements

## 3.3 Logs and events

Used to record:

* Policy denial
* Approval request
* Provider schema drift
* Tool quarantine
* Evaluation failure
* Tool confusion
* Budget exhaustion
* Canary rollback
* Effect uncertainty

## 3.4 Profiles

Used selectively for:

* CPU-intensive calculations
* Large parsers
* Code-execution tools
* Retrieval ranking
* Embedding generation
* High-volume data transformations

## 3.5 Evaluation records

Used to represent:

* Test case
* Expected behaviour
* Observed behaviour
* Scoring method
* Evaluator
* Evidence
* Pass or failure
* Regression relationship
* Reproducibility information

---

# 4. Telemetry hierarchy

Every execution should be traceable through a single causal hierarchy.

```text id="1tn3ac"
User objective
    ↓
Agent session
    ↓
Root graph run
    ↓
Graph node
    ↓
Capability discovery
    ↓
Tool selection
    ↓
Tool invocation
    ↓
Maintenance execution
    ↓
Provider / model / internal-tool call
    ↓
Output and effect verification
    ↓
Graph completion
    ↓
User-facing outcome
```

An evaluation run may replay or inspect any level of this hierarchy.

---

# 5. Required correlation identifiers

```typescript id="k7vd33"
export interface ServiceFabricCorrelation {
  traceId: string;
  spanId: string;

  sessionId?: string;

  rootGraphRunId?: string;
  graphRunId?: string;
  graphNodeRunId?: string;

  toolDiscoveryId?: string;
  toolSelectionId?: string;
  toolInvocationId?: string;

  maintenanceRunId?: string;
  providerCallId?: string;
  modelCallId?: string;

  approvalId?: string;
  effectId?: string;

  evaluationRunId?: string;
  experimentId?: string;
  incidentId?: string;
}
```

Every significant resource should contain enough identifiers to move between:

```text id="a221vl"
Trace
Evaluation
Incident
Approval
Effect receipt
Tool revision
Graph revision
Evolution run
```

---

# 6. Telemetry context propagation

The ServiceFabric runtime should propagate:

* W3C trace context
* ServiceFabric correlation identifiers
* Tenant-safe execution metadata
* Tool and graph revision identifiers
* Invocation deadline
* Budget identifiers

OpenTelemetry baggage can propagate contextual key-value information across services and processes, but ServiceFabric should restrict baggage to non-sensitive routing and correlation metadata.

## 6.1 Permitted propagated fields

```text id="ib7j3h"
servicefabric.root_graph_run_id
servicefabric.graph_run_id
servicefabric.tool_invocation_id
servicefabric.tool_id
servicefabric.tool_revision_id
servicefabric.tenant_hash
servicefabric.environment
servicefabric.experiment_id
servicefabric.policy_decision_id
```

## 6.2 Prohibited baggage fields

```text id="97n47z"
Access tokens
API keys
User messages
Document contents
Email addresses
Payment instructions
Personal identifiers
Approval contents
Confidential arguments
Provider payloads
```

Sensitive values should remain in protected stores and be referenced through opaque identifiers.

---

# 7. ServiceFabric semantic conventions

ServiceFabric should reserve:

```text id="7tkk31"
servicefabric.*
```

as its telemetry namespace.

## 7.1 Resource attributes

```text id="rt3dns"
servicefabric.service.name
servicefabric.service.version
servicefabric.environment
servicefabric.region
servicefabric.tenant_scope
servicefabric.runtime.type
servicefabric.runtime.version
```

## 7.2 Graph attributes

```text id="h0jofr"
servicefabric.graph.id
servicefabric.graph.version
servicefabric.graph.revision_id
servicefabric.graph.run_id
servicefabric.graph.node.id
servicefabric.graph.node.type
servicefabric.graph.depth
servicefabric.graph.outcome
```

## 7.3 Tool attributes

```text id="87ja2t"
servicefabric.tool.id
servicefabric.tool.version
servicefabric.tool.revision_id
servicefabric.tool.capability_class
servicefabric.tool.effect_class
servicefabric.tool.agentic_level
servicefabric.tool.outcome
servicefabric.tool.error_code
servicefabric.tool.partial
```

## 7.4 Model-call attributes

```text id="160yvd"
servicefabric.model.provider
servicefabric.model.configuration_id
servicefabric.model.purpose
servicefabric.model.input_tokens
servicefabric.model.output_tokens
servicefabric.model.cached_tokens
servicefabric.model.cost_usd
servicefabric.model.structured_output_valid
servicefabric.model.retry_count
```

Raw prompts, responses and hidden reasoning must not be included as ordinary span attributes.

## 7.5 Provider attributes

```text id="p2x8iv"
servicefabric.provider.id
servicefabric.provider.operation
servicefabric.provider.request_id
servicefabric.provider.status
servicefabric.provider.latency_ms
servicefabric.provider.cost_usd
servicefabric.provider.schema_hash
servicefabric.provider.fallback
```

## 7.6 Governance attributes

```text id="b9hk24"
servicefabric.policy.decision_id
servicefabric.policy.result
servicefabric.policy.reason_codes
servicefabric.approval.required
servicefabric.approval.satisfied
servicefabric.effect.class
servicefabric.effect.status
servicefabric.effect.verified
```

---

# 8. Span model

Recommended span topology:

```text id="spj0f0"
agent.objective
└── graph.run
    ├── graph.node
    ├── registry.search_capabilities
    ├── registry.select_tool
    ├── policy.evaluate
    ├── tool.invoke
    │   ├── maintenance.preflight
    │   ├── adapter.execute
    │   │   ├── provider.call
    │   │   ├── model.call
    │   │   └── internal_tool.call
    │   ├── maintenance.recovery
    │   ├── output.validate
    │   ├── evidence.verify
    │   └── effect.verify
    └── graph.complete
```

## 8.1 Span naming

Use stable operation names:

```text id="976gu1"
graph.run
graph.node.execute
registry.capability.search
registry.tool.resolve
policy.evaluate
approval.verify
tool.invoke
tool.validate_input
tool.validate_output
maintenance.select_plan
maintenance.retry
maintenance.fallback
provider.call
model.generate
effect.verify
evaluation.case
evaluation.score
experiment.assign
```

Dynamic values belong in attributes, not span names.

Bad:

```text id="yq10cg"
tool.invoke research.search_papers
```

Preferred:

```text id="mzrcc1"
span name:
    tool.invoke

attribute:
    servicefabric.tool.id = research.search_papers
```

---

# 9. Graph trace model

```typescript id="3248ze"
export interface GraphRunTelemetry {
  graphRunId: string;

  graphId: string;
  graphVersion: string;
  graphRevisionId: string;

  rootGraphRunId: string;
  parentGraphRunId?: string;

  objectiveClass: string;
  callerClass: string;

  startedAt: string;
  completedAt?: string;

  status:
    | "running"
    | "succeeded"
    | "partial"
    | "failed"
    | "cancelled"
    | "awaiting_input"
    | "awaiting_approval";

  nodeCount: number;
  toolCallCount: number;
  modelCallCount: number;

  durationMs?: number;
  totalCostUsd?: number;

  finalOutcomeRef?: string;
}
```

## 9.1 Graph-node telemetry

```typescript id="pbyn0u"
export interface GraphNodeTelemetry {
  graphNodeRunId: string;
  graphRunId: string;

  nodeId: string;
  nodeType: string;

  attempt: number;

  startedAt: string;
  completedAt?: string;

  outcome: string;

  inputArtifactRefs: string[];
  outputArtifactRefs: string[];

  selectedRoute?: string;

  errorCode?: string;
}
```

---

# 10. Tool-discovery telemetry

The registry should record the discovery process without retaining full sensitive objectives by default.

```typescript id="r1pxe4"
export interface ToolDiscoveryTelemetry {
  discoveryId: string;
  graphRunId?: string;

  queryClass: string;
  queryHash: string;

  candidateCountRetrieved: number;
  candidateCountAuthorized: number;
  candidateCountRanked: number;
  candidateCountPresented: number;

  presentedToolIds: string[];

  selectedToolId?: string;
  selectedRank?: number;

  gapReturned: boolean;

  durationMs: number;
}
```

## 10.1 Discovery quality signals

* Correct tool appeared in candidate set.
* Correct tool appeared in top three.
* Selected tool was the highest-ranked valid tool.
* Tool catalogue was unnecessarily large.
* Unauthorized tools were filtered.
* Tool gap was correctly identified.
* Provider variants were appropriately hidden.
* Deprecated tools were avoided.

---

# 11. Tool-selection record

```typescript id="43n2ds"
export interface ToolSelectionRecord {
  selectionId: string;

  graphRunId: string;
  graphNodeId: string;

  objectiveClass: string;

  candidateToolIds: string[];
  selectedToolId?: string;

  decisionSource:
    | "deterministic"
    | "model"
    | "human"
    | "compiled_dependency";

  reasonCodes: string[];

  confidence?: number;

  noToolSelected: boolean;

  selectedAt: string;
}
```

The model’s full private reasoning is not required. The system stores structured reasons and relevant evidence.

---

# 12. Tool-invocation telemetry

```typescript id="9pv11x"
export interface ToolInvocationTelemetry {
  invocationId: string;

  toolId: string;
  toolVersion: string;
  revisionId: string;

  graphRunId?: string;
  selectionId?: string;

  argumentSchemaValid: boolean;
  argumentHash: string;

  effectClass: string;
  approvalRequired: boolean;
  approvalSatisfied: boolean;

  providerIds: string[];

  attemptCount: number;
  retryCount: number;
  fallbackCount: number;

  modelCallCount: number;
  internalToolCallCount: number;

  status:
    | "success"
    | "partial"
    | "error"
    | "cancelled"
    | "uncertain";

  errorCode?: string;

  outputSchemaValid: boolean;
  evidenceCoverage?: number;
  effectVerified?: boolean;

  durationMs: number;
  costUsd?: number;
}
```

---

# 13. Error telemetry

Errors should be recorded through stable ServiceFabric codes.

```typescript id="cyed5q"
export interface ErrorTelemetry {
  errorCode: string;
  errorCategory: string;

  layer:
    | "protocol"
    | "registry"
    | "policy"
    | "approval"
    | "input_validation"
    | "maintenance"
    | "implementation"
    | "provider"
    | "model"
    | "output_validation"
    | "effect_verification"
    | "graph";

  retryable: boolean;
  recovered: boolean;

  recoveryAction?:
    | "argument_repair"
    | "retry"
    | "fallback"
    | "partial_result"
    | "human_escalation"
    | "rollback";

  safeMessage: string;
  incidentId?: string;
}
```

Protocol-level MCP errors and tool-execution errors should remain separately measurable because they indicate different problems:

```text id="v6r2u4"
Protocol error
    Integration or transport defect

Tool error
    Caller, domain, provider or execution defect
```

MCP’s tool specification supports structured tool results and explicitly distinguishes tool execution errors from protocol errors.

---

# 14. High-cardinality controls

Telemetry systems can become unusable if uncontrolled values are stored as indexed attributes.

Do not use these as metric labels:

```text id="n1ks67"
User identifier
Invocation identifier
Document identifier
Exact query
URL
Repository path
Email address
Error message
Provider request identifier
```

Use:

* Traces for individual high-cardinality executions
* Logs for discrete records
* Metrics for bounded dimensions
* Hashes or classes rather than raw content
* Exemplars to connect aggregated metrics to sample traces

Recommended metric dimensions:

```text id="ir91iq"
tool_id
tool_version
capability_class
effect_class
environment
region
outcome
error_category
provider_id
agentic_level
```

---

# 15. Metrics taxonomy

ServiceFabric metrics should be grouped into seven families.

```text id="cxjstn"
Operational
Contract
Agent-callability
Graph outcome
Safety and governance
Economic
Evolution
```

---

# 16. Operational metrics

```text id="gcbe45"
servicefabric_tool_invocations_total
servicefabric_tool_success_total
servicefabric_tool_partial_total
servicefabric_tool_errors_total
servicefabric_tool_latency_ms
servicefabric_tool_queue_latency_ms

servicefabric_provider_calls_total
servicefabric_provider_errors_total
servicefabric_provider_latency_ms
servicefabric_provider_rate_limits_total

servicefabric_model_calls_total
servicefabric_model_latency_ms
servicefabric_model_tokens_total

servicefabric_graph_runs_total
servicefabric_graph_duration_ms
servicefabric_graph_node_executions_total
```

## 16.1 Availability

```text id="kmne7m"
successful valid tool outcomes
────────────────────────────────
eligible invocation attempts
```

Policy denials should generally not count as availability failures.

## 16.2 Reliability

Measure separately:

* Technical execution success
* Contract-valid success
* Domain-valid success
* Effect-verified success

A tool that returns HTTP 200 with invalid structured content is not reliable.

---

# 17. Contract metrics

```text id="83s4io"
servicefabric_input_schema_validity_rate
servicefabric_output_schema_validity_rate
servicefabric_error_code_conformance_rate
servicefabric_evidence_coverage_rate
servicefabric_effect_verification_rate
servicefabric_partial_result_validity_rate
servicefabric_idempotency_success_rate
```

Required production targets for native tools should ordinarily include:

```text id="cld1zb"
Output schema validity: 100%
Stable error-code conformance: 100%
Effect verification for declared writes: 100%
Authorization audit record rate: 100%
```

A quality score cannot compensate for a contract violation.

---

# 18. Agent-callability metrics

```text id="xj1u0x"
servicefabric_tool_selection_precision
servicefabric_tool_selection_recall
servicefabric_tool_selection_top1_accuracy
servicefabric_tool_selection_top3_recall
servicefabric_no_tool_accuracy

servicefabric_argument_validity_rate
servicefabric_argument_semantic_accuracy
servicefabric_argument_repair_rate

servicefabric_result_interpretation_accuracy
servicefabric_partial_result_interpretation_accuracy
servicefabric_error_recovery_accuracy

servicefabric_unnecessary_tool_call_rate
servicefabric_unsafe_tool_selection_rate
servicefabric_tool_confusion_rate
```

---

# 19. Selection precision and recall

## 19.1 Tool-selection precision

```text id="b3h184"
valid selected tool calls
─────────────────────────
all selected tool calls
```

This penalizes unnecessary or inappropriate calls.

## 19.2 Tool-selection recall

```text id="r4xxpk"
tasks where a valid required tool was selected
─────────────────────────────────────────────
tasks requiring that tool capability
```

## 19.3 Top-k recall

Useful for registry evaluation:

```text id="vljt8f"
tasks where an acceptable tool appears in top k
───────────────────────────────────────────────
tasks with an acceptable registered tool
```

## 19.4 No-tool accuracy

Some objectives should not use a tool.

```text id="h5n85c"
correct no-tool decisions
─────────────────────────
tasks requiring no tool
```

This prevents an evaluation system from rewarding tool use merely because a tool was called.

---

# 20. Tool usefulness

Selection correctness alone is insufficient.

A technically suitable tool may still fail to advance the task.

```typescript id="j6zcq2"
export interface ToolUsefulnessAssessment {
  invocationId: string;

  objectiveProgress:
    | "none"
    | "minor"
    | "material"
    | "completed";

  outputUsedByGraph: boolean;

  subsequentCorrectionRequired: boolean;

  replacementToolCalled: boolean;

  contributedToFinalOutcome: boolean;

  score: number;
}
```

Useful online proxies include:

* Was the result consumed by a later node?
* Did the graph immediately replace it with another tool?
* Did the user correct the result?
* Did the graph complete successfully?
* Did the tool reduce uncertainty?
* Did the result provide required evidence?

---

# 21. Argument evaluation

Argument quality has two layers.

```text id="94w63i"
Syntactic validity
    Does the argument match the schema?

Semantic validity
    Does it correctly represent the objective?
```

A call may be schema-valid but semantically wrong.

Example:

```text id="n96vop"
Objective:
    Search papers published after 2024.

Schema-valid arguments:
    publishedBefore = 2024-01-01

Result:
    Syntactically valid, semantically incorrect.
```

## 21.1 Argument evaluation record

```typescript id="szf05r"
export interface ArgumentEvaluation {
  invocationId: string;

  schemaValid: boolean;
  semanticValid: boolean;

  requiredFieldAccuracy: number;
  optionalFieldAccuracy: number;

  unnecessaryFields: string[];
  omittedMaterialFields: string[];

  repairAttempts: number;
  repairedSuccessfully: boolean;

  score: number;
}
```

---

# 22. Result-interpretation evaluation

The framework should test whether the calling agent correctly understands:

* `success`
* `partial`
* `error`
* Warnings
* Provenance
* Confidence
* Freshness
* Effect receipts
* Retryability
* Suggested repair
* Missing data

```typescript id="84q5s1"
export interface ResultInterpretationEvaluation {
  invocationId: string;

  statusInterpretedCorrectly: boolean;
  warningsAcknowledged: boolean;
  evidenceUsedCorrectly: boolean;

  missingDataRecognized: boolean;
  staleDataRecognized: boolean;

  retryDecisionCorrect: boolean;
  effectStateInterpretedCorrectly: boolean;

  unsupportedClaimsIntroduced: boolean;

  score: number;
}
```

---

# 23. Evidence-faithfulness evaluation

For research, finance, organisational analysis and management reporting, the framework must evaluate whether outputs remain grounded in tool evidence.

```typescript id="ad9u51"
export interface EvidenceFaithfulnessEvaluation {
  outputArtifactId: string;

  claimCount: number;
  supportedClaimCount: number;
  unsupportedClaimCount: number;
  contradictedClaimCount: number;

  evidenceCoverage: number;
  citationValidity: number;
  sourceAttributionAccuracy: number;

  materialUnsupportedClaims: string[];

  score: number;
}
```

## 23.1 Evidence requirements

Evidence evaluation should distinguish:

* Source exists
* Source supports the claim
* Source is sufficiently current
* Source is authoritative enough
* Citation points to the correct location
* Calculation can be reproduced
* Effect receipt belongs to this invocation

---

# 24. Graph outcome metrics

```text id="09sscg"
servicefabric_graph_completion_rate
servicefabric_graph_partial_completion_rate
servicefabric_graph_failure_rate
servicefabric_graph_user_correction_rate
servicefabric_graph_human_escalation_rate
servicefabric_graph_replanning_rate
servicefabric_graph_average_tool_calls
servicefabric_graph_average_model_calls
servicefabric_graph_loop_detection_total
servicefabric_graph_budget_exhaustion_rate
```

## 24.1 Graph completion

A graph succeeds only when its declared completion criteria are met.

Examples:

```text id="o1zu47"
Research graph:
    Evidence set satisfies minimum coverage.

Project graph:
    Requested task exists and is verified.

Financial analysis graph:
    Required calculations and report are complete.

Software graph:
    Defect is reproduced and proposed change passes tests.
```

## 24.2 Graph efficiency

Measure:

```text id="9atqy4"
Tool calls per completed objective
Model calls per completed objective
Tokens per completed objective
Cost per completed objective
Elapsed time per completed objective
Retries per completed objective
```

Efficiency should never reward skipping required safety or evidence steps.

---

# 25. Safety and governance metrics

```text id="xefj4l"
servicefabric_policy_decisions_total
servicefabric_policy_denials_total
servicefabric_approval_requests_total
servicefabric_approval_binding_failures_total

servicefabric_unauthorized_effects_total
servicefabric_uncertain_effects_total
servicefabric_effect_reconciliations_total

servicefabric_cross_tenant_denials_total
servicefabric_prompt_injection_blocks_total
servicefabric_secret_access_denials_total

servicefabric_quarantine_events_total
servicefabric_security_incidents_total
```

Absolute safety invariants should not be averaged into a broad quality score.

For example:

```text id="srqve0"
One unauthorized payment
    cannot be offset by
one thousand highly relevant search results.
```

---

# 26. Economic telemetry

```typescript id="z3d30h"
export interface ExecutionCostRecord {
  executionId: string;

  toolCostUsd: number;
  modelCostUsd: number;
  providerCostUsd: number;
  infrastructureCostUsd?: number;

  inputTokens?: number;
  outputTokens?: number;
  cachedTokens?: number;

  providerRequests: number;
  internalToolCalls: number;

  attributedObjectiveId?: string;
}
```

## 26.1 Cost attribution hierarchy

```text id="f2xkvv"
Provider or model call
    ↓
Tool invocation
    ↓
Graph node
    ↓
Graph run
    ↓
User objective
    ↓
Project / tenant / cost centre
```

## 26.2 Economic metrics

```text id="hdhu39"
cost_per_tool_success
cost_per_graph_completion
cost_per_valid_evidence_item
cost_per_verified_effect
cost_per_research_result
cost_per_resolved_incident
cost_of_retries
cost_of_fallbacks
cost_of_invalid_calls
cost_of_agent_confusion
```

This makes unnecessary reasoning and repeated tool calls economically visible.

---

# 27. Quality score architecture

A ServiceFabric tool may have several independent quality dimensions.

```typescript id="z94ux7"
export interface ToolQualityVector {
  operationalReliability: number;
  contractConformance: number;
  domainAccuracy: number;
  agentCallability: number;
  evidenceQuality: number;
  safety: number;
  efficiency: number;
  maintainability: number;
}
```

Do not immediately collapse this vector into one number.

A summary score may exist for ranking, but critical dimensions should retain minimum thresholds.

```text id="6zhljw"
Eligible for publication only when:

contractConformance ≥ threshold
AND safety = required threshold
AND domainAccuracy ≥ threshold
AND agentCallability ≥ threshold
```

A weighted average is appropriate only after mandatory gates pass.

---

# 28. Evaluation layers

ServiceFabric should evaluate at six layers.

```text id="12waeg"
Layer 1 — Function
    Does the primitive implementation work?

Layer 2 — Tool contract
    Does the capsule satisfy its interface?

Layer 3 — Agent callability
    Can agents select and invoke it?

Layer 4 — Graph behaviour
    Does it compose successfully?

Layer 5 — Objective outcome
    Does the system satisfy user intent?

Layer 6 — Operational ecosystem
    Does it remain safe and useful in production?
```

---

# 29. Evaluation modes

```typescript id="g4j5ns"
export type EvaluationMode =
  | "unit"
  | "contract"
  | "integration"
  | "simulation"
  | "offline_benchmark"
  | "historical_replay"
  | "shadow"
  | "canary"
  | "online_monitoring"
  | "human_review";
```

## 29.1 Unit

Tests deterministic internal behaviour.

## 29.2 Contract

Tests schemas, errors, invariants and Tool Capsule behaviour.

## 29.3 Integration

Tests real or controlled dependencies.

## 29.4 Simulation

Tests tools and graphs against provider and environment simulators.

## 29.5 Offline benchmark

Tests fixed datasets and expected outcomes.

## 29.6 Historical replay

Replays prior invocations under privacy controls.

## 29.7 Shadow

Runs a candidate without serving its result or committing effects.

## 29.8 Canary

Serves a controlled portion of eligible production calls.

## 29.9 Online monitoring

Uses production telemetry and sampled evaluations.

## 29.10 Human review

Used for ambiguity, materiality, domain judgment and high-risk outcomes.

---

# 30. Evaluation resource model

```text id="r8h044"
EvaluationSuite
    Collection of evaluation cases

EvaluationCase
    One objective and expected behaviour

EvaluationRun
    Execution of a suite against a target

EvaluationObservation
    Raw recorded behaviour

EvaluationScore
    Derived metric or judgment

EvaluationReport
    Aggregated conclusions and gates
```

---

# 31. EvaluationSuite

```typescript id="thb868"
export interface EvaluationSuite {
  suiteId: string;
  version: string;

  title: string;
  description: string;

  targetType:
    | "tool"
    | "graph"
    | "registry"
    | "maintenance_graph"
    | "policy"
    | "model_configuration";

  targetId: string;

  categories: EvaluationCategory[];

  caseRefs: string[];

  scoringPolicyRef: string;
  publicationThresholds: EvaluationThreshold[];

  createdAt: string;
  contentHash: string;
}
```

---

# 32. Evaluation categories

```typescript id="z0fe2c"
export type EvaluationCategory =
  | "selection"
  | "negative_selection"
  | "arguments"
  | "execution"
  | "output_contract"
  | "domain_accuracy"
  | "evidence"
  | "interpretation"
  | "recovery"
  | "composition"
  | "security"
  | "governance"
  | "effects"
  | "performance"
  | "cost"
  | "robustness"
  | "migration";
```

---

# 33. EvaluationCase

```typescript id="me7yls"
export interface EvaluationCase {
  caseId: string;
  version: string;

  title: string;
  category: EvaluationCategory;

  objective: string;

  callerProfile: string;
  authorityProfile: string;

  initialContextRefs: string[];

  availableToolIds?: string[];
  availableCapabilityIds?: string[];

  expected: ExpectedEvaluationBehaviour;

  prohibited: ProhibitedEvaluationBehaviour[];

  environmentFixtureRef?: string;
  providerFixtureRefs?: string[];

  labels: string[];

  riskLevel: "low" | "medium" | "high" | "critical";

  createdFrom?:
    | "design"
    | "incident"
    | "production_failure"
    | "security_test"
    | "user_feedback"
    | "evolution_signal";

  createdAt: string;
}
```

---

# 34. Expected evaluation behaviour

```typescript id="toh90h"
export interface ExpectedEvaluationBehaviour {
  acceptableToolIds?: string[];
  requiredToolIds?: string[];
  prohibitedToolIds?: string[];

  noToolExpected?: boolean;

  expectedArguments?: ArgumentExpectation[];

  expectedResultProperties?: ResultExpectation[];

  expectedGraphOutcome?: string;

  expectedEvidence?: EvidenceExpectation[];

  expectedEffects?: ProposedEffect[];

  expectedErrorCodes?: string[];

  maximumToolCalls?: number;
  maximumModelCalls?: number;
  maximumCostUsd?: number;
  maximumDurationMs?: number;
}
```

---

# 35. EvaluationObservation

```typescript id="jn0t5w"
export interface EvaluationObservation {
  evaluationRunId: string;
  caseId: string;

  targetRevisionId: string;

  graphRunId?: string;
  traceId: string;

  selectedTools: string[];
  toolInvocations: string[];

  modelCalls: string[];
  providerCalls: string[];

  finalOutcomeRef?: string;

  effects: ObservedEffect[];

  errors: string[];

  totalDurationMs: number;
  totalCostUsd: number;

  capturedAt: string;
}
```

---

# 36. Evaluation scoring

Scorers may be:

```typescript id="crahym"
export type EvaluatorType =
  | "deterministic"
  | "reference_comparison"
  | "statistical"
  | "model_judge"
  | "human_expert"
  | "hybrid";
```

## 36.1 Deterministic evaluator

Preferred for:

* Schema validity
* Exact calculations
* Required tool selection
* Error-code conformance
* Authorization
* Approval
* Side effects
* Cost limits
* Latency thresholds

## 36.2 Reference comparison

Used for:

* Known financial calculations
* Structured extraction
* Expected code output
* Retrieval identifier validity
* Reconciliation results

## 36.3 Statistical evaluator

Used for:

* Ranking quality
* Search relevance
* Provider agreement
* Online experiments
* Performance distributions

## 36.4 Model judge

Used only when deterministic evaluation is insufficient.

Appropriate for:

* Relevance
* Explanation quality
* Completeness
* Semantic argument accuracy
* Whether an answer acknowledges missing evidence

## 36.5 Human expert

Used for:

* Legal meaning
* Material financial interpretation
* Organisational recommendations
* Ambiguous research synthesis
* High-impact management decisions

## 36.6 Hybrid

Combines:

```text id="4wyxy2"
Deterministic contract gates
        +
Model semantic scoring
        +
Human audit sample
```

---

# 37. Model-judge controls

A model judge must not be treated as ground truth.

```typescript id="0x2r0s"
export interface ModelJudgeConfiguration {
  judgeConfigurationId: string;

  purpose: string;

  rubricRef: string;
  outputSchemaRef: string;

  blindedToTargetIdentity: boolean;
  randomizedPresentationOrder: boolean;

  repetitions: number;

  disagreementPolicy: string;

  humanAuditRate: number;

  maximumTokens: number;
  maximumCostUsd: number;
}
```

## 37.1 Judge bias controls

* Blind baseline and candidate identities.
* Randomize output order.
* Use structured rubrics.
* Include counterexamples.
* Calibrate against expert-labeled cases.
* Measure inter-judge agreement.
* Audit material disagreements.
* Avoid using the same configuration as sole generator and sole judge.
* Do not use model judgment for authorization or effect correctness.

---

# 38. Evaluation rubric

```typescript id="a7p39e"
export interface EvaluationRubric {
  rubricId: string;
  version: string;

  dimensions: Array<{
    id: string;
    description: string;

    scoreLevels: Array<{
      score: number;
      criteria: string;
    }>;

    weight: number;
    mandatoryMinimum?: number;
  }>;

  terminalFailures: Array<{
    condition: string;
    reasonCode: string;
  }>;
}
```

Example dimensions for research search:

```text id="puovwh"
Query interpretation
Result relevance
Identifier validity
Provenance completeness
Freshness
Deduplication
Partial-result disclosure
```

Terminal failures:

```text id="op6fe9"
Fabricated citation
Missing provenance for returned item
Unauthorized data disclosure
Output schema violation
```

---

# 39. Agent-callability evaluation suite

Every public tool requires at least five case groups.

```text id="fzhiww"
Positive selection
Negative selection
Argument construction
Result interpretation
Recovery and composition
```

## 39.1 Positive selection cases

Test whether the agent selects the tool for:

* Direct requests
* Paraphrases
* Domain-specific wording
* Requests embedded within larger objectives
* Situations where inputs are already available
* Situations requiring the tool after another tool

## 39.2 Negative selection cases

Test whether the agent avoids the tool for:

* Similar but unsupported tasks
* Requests requiring a different effect
* Requests with missing prerequisites
* Tasks requiring no tool
* Tasks requiring a human
* Tasks outside authorization
* Tasks where the tool is unavailable

## 39.3 Argument cases

Include:

* Typical input
* Optional parameters
* Boundary values
* Dates
* Identifiers
* Ambiguous input
* Unsupported values
* Missing required information
* Approval-sensitive arguments

## 39.4 Interpretation cases

Include:

* Success
* Partial result
* Retryable error
* Terminal error
* Stale data
* Missing source
* Effect uncertainty
* Approval denial
* Conflicting evidence

## 39.5 Composition cases

Test:

* Correct predecessor tool
* Correct successor tool
* Avoiding redundant calls
* Avoiding loops
* Passing structured outputs correctly
* Respecting effect sequence
* Recognizing when a composite tool is preferable

---

# 40. Tool-confusion suite

Every pair of similar tools should have explicit differentiation tests.

```typescript id="7yt6go"
export interface ToolConfusionCase {
  caseId: string;

  candidateToolIds: string[];

  objective: string;

  correctToolIds: string[];
  prohibitedToolIds: string[];

  differentiatingFactors: string[];
}
```

Example:

```text id="iie8u3"
research.search_papers
    Discovers scholarly records.

research.retrieve_paper
    Retrieves a known document.

research.verify_quotation
    Checks whether wording appears in a known source.
```

The suite should include requests that differ by only one decisive detail.

---

# 41. Graph-level evaluation

A graph must be evaluated as an orchestration system, not as the sum of its tools.

Evaluation dimensions:

```text id="znwmcw"
Planning quality
Tool selection
Ordering
State management
Budget control
Recovery
Stopping behaviour
Evidence integration
Final outcome
Safety
```

## 41.1 Plan quality

Measure whether the graph:

* Identifies required subtasks
* Avoids unnecessary subtasks
* Places approval before effects
* Places verification after effects
* Uses bounded parallelism
* Identifies missing information
* Chooses an appropriate stopping condition

## 41.2 Ordering

Examples of invalid ordering:

```text id="0ih8k3"
Submit transaction
    before approval

Generate report
    before retrieving required data

Retry write
    before effect reconciliation

Publish result
    before evidence verification
```

## 41.3 Loop and termination testing

Test:

* Repeated tool calls
* Repeated planning
* Provider fallback cycles
* Invalid argument repair cycles
* Subgraph recursion
* Repeated user clarification
* Retry after terminal error

Each graph requires measurable stopping conditions.

---

# 42. Agent-recovery evaluation

```typescript id="cohjki"
export interface RecoveryEvaluation {
  initialFailureClass: string;

  expectedRecoveryActions: string[];
  prohibitedRecoveryActions: string[];

  observedActions: string[];

  recovered: boolean;
  attempts: number;

  budgetRespected: boolean;
  effectSafetyPreserved: boolean;

  score: number;
}
```

Evaluate recovery from:

* Invalid argument
* Tool unavailable
* Provider timeout
* Rate limit
* Partial result
* Missing evidence
* Model malformed output
* Approval required
* Effect uncertain
* User correction

Successful recovery means resolving or safely surfacing the failure—not merely making more calls.

---

# 43. Security evaluation

Security tests should include:

```text id="26c0he"
Prompt injection
Tool-result injection
Description injection
Unauthorized tool discovery
Unauthorized invocation
Authority-chain expansion
Cross-tenant access
Secret extraction
Provider-token misuse
Approval forgery
Effect manipulation
Budget amplification
Recursive tool calls
Sandbox escape
Audit suppression
```

## 43.1 Security scoring

Security tests should primarily use:

```text id="mmxkwx"
pass
fail
not_applicable
```

rather than soft numerical scores.

One critical failure blocks publication or causes quarantine.

## 43.2 Adversarial evaluation case

```typescript id="a1elvj"
export interface AdversarialEvaluationCase
  extends EvaluationCase {
  attackClass: string;

  adversarialPayloadRef: string;

  expectedControl: string;

  compromiseIndicators: string[];

  severity: "medium" | "high" | "critical";
}
```

---

# 44. Side-effect evaluation

Effectful tools require simulation and verification.

```text id="en6e8l"
Proposal
    ↓
Approval
    ↓
Execution
    ↓
Observed effect
    ↓
Verification
    ↓
Receipt
```

Tests include:

* Correct target
* Incorrect target rejection
* Amount or magnitude limit
* Recipient change after approval
* Duplicate invocation
* Provider timeout before commit
* Provider timeout after commit
* Partial multi-target effect
* Rollback
* Reconciliation
* Forged receipt

No effectful tool can pass solely through mocked return values. At least one controlled integration environment must verify actual postconditions.

---

# 45. Performance evaluation

Performance tests should measure distributions rather than averages.

```text id="k77l53"
p50
p90
p95
p99
maximum
```

Evaluate:

* End-to-end latency
* Maintenance overhead
* Policy latency
* Registry latency
* Provider latency
* Model latency
* Queue time
* Output-validation time
* Evidence-verification time
* Effect-verification time

## 45.1 Latency budget

```typescript id="xujd4v"
export interface LatencyBudget {
  totalMs: number;

  registryMs: number;
  policyMs: number;
  maintenanceMs: number;
  executionMs: number;
  validationMs: number;
  effectVerificationMs?: number;
}
```

This identifies whether an agentic tool is slow because of:

* Model reasoning
* Provider calls
* Excessive retries
* Registry discovery
* Policy decisions
* Validation
* Poor graph design

---

# 46. Load and resilience evaluation

Test:

* Concurrent tool calls
* Tenant isolation under load
* Provider rate limiting
* Queue saturation
* Circuit breakers
* Backpressure
* Partial dependency failure
* Telemetry collector outage
* Registry cache use
* Policy service latency
* Evaluation service unavailability

Telemetry failures must not silently disable safety enforcement.

The system may degrade non-essential telemetry, but must preserve:

* Policy decisions
* Approval records
* Effect receipts
* Critical audit events
* Security incidents

---

# 47. Evaluation datasets

Evaluation datasets should be:

* Versioned
* Immutable per version
* Traceable to sources
* Classified
* Deduplicated
* Balanced across normal and adversarial cases
* Split to prevent overfitting
* Reviewed for leakage

```typescript id="xh7yli"
export interface EvaluationDataset {
  datasetId: string;
  version: string;

  domain: string;

  caseRefs: string[];

  classifications: string[];

  sourceTypes: string[];

  trainCaseRefs?: string[];
  developmentCaseRefs?: string[];
  holdoutCaseRefs: string[];

  accessPolicyRef: string;

  contentHash: string;
}
```

## 47.1 Dataset partitions

```text id="6xan07"
Development set
    Used during construction.

Regression set
    Historical failures and incidents.

Holdout set
    Hidden from generation and repair agents.

Adversarial set
    Security and robustness testing.

Production audit sample
    Controlled sample of real outcomes.
```

---

# 48. Incident-to-evaluation conversion

Every material incident should generate at least one permanent regression case.

```text id="jdbyrv"
Production incident
      ↓
Evidence preservation
      ↓
Minimal reproducible case
      ↓
Sensitive-data transformation
      ↓
Regression evaluation case
      ↓
Added to relevant suites
```

```typescript id="ab0y0z"
export interface IncidentEvaluationLink {
  incidentId: string;

  generatedCaseIds: string[];

  reproductionEnvironment: string;

  confidentialityControls: string[];

  verifiedBy: string;

  createdAt: string;
}
```

This prevents fixes from relying only on temporary operational knowledge.

---

# 49. User-feedback integration

User corrections can indicate:

* Wrong tool selection
* Incorrect result
* Poor explanation
* Missing evidence
* Excessive tool use
* Unsafe action proposal
* Misunderstood objective

Feedback should be classified before entering evaluation.

```typescript id="29efj5"
export interface UserFeedbackRecord {
  feedbackId: string;

  graphRunId?: string;
  toolInvocationId?: string;

  feedbackType:
    | "incorrect"
    | "incomplete"
    | "wrong_tool"
    | "unsafe"
    | "too_slow"
    | "too_costly"
    | "poor_explanation"
    | "positive";

  severity: string;

  userCommentRef?: string;

  validated: boolean;
  evaluationCaseCreated: boolean;

  createdAt: string;
}
```

A single subjective correction should not automatically change routing, but repeated validated feedback can trigger evolution.

---

# 50. Online evaluation

Not every production execution should undergo expensive semantic judging.

ServiceFabric should use risk-based sampling.

```typescript id="x1omfp"
export interface OnlineEvaluationSamplingPolicy {
  toolId?: string;
  graphId?: string;

  baselineSampleRate: number;

  increasedSampleRateWhen:
    | Array<
        | "new_revision"
        | "canary"
        | "quality_decline"
        | "incident"
        | "high_risk"
        | "new_provider"
        | "model_change"
      >;

  maximumDailyCases: number;

  sensitiveDataPolicyRef: string;
}
```

## 50.1 Mandatory evaluation cases

Always evaluate or audit:

* Canary high-risk effects
* Uncertain effects
* Security-policy failures
* New provider schema
* Output-schema violation
* Material user correction
* Tool quarantine candidate
* Financial-limit boundary cases

---

# 51. Shadow evaluation

```text id="6y44m3"
Production input
    ↓
Baseline revision → authoritative result
    ↓
Redacted copy
    ↓
Candidate revision → non-authoritative result
    ↓
Comparative evaluator
```

Compare:

* Tool selection
* Arguments
* Result validity
* Evidence
* Latency
* Cost
* Model calls
* Provider calls
* Safety
* Effect proposal

Shadow candidates must not commit real effects.

---

# 52. Canary evaluation

A canary report should include:

```typescript id="6fplrb"
export interface CanaryEvaluationReport {
  experimentId: string;

  baselineRevisionId: string;
  candidateRevisionId: string;

  observationWindow: {
    from: string;
    to: string;
  };

  baselineSampleSize: number;
  candidateSampleSize: number;

  primaryMetrics: MetricComparison[];
  guardrailMetrics: MetricComparison[];

  affectedCallerSegments: string[];

  incidents: string[];

  decision:
    | "expand"
    | "continue"
    | "reduce"
    | "rollback"
    | "promote";

  reasonCodes: string[];
}
```

No candidate may be promoted solely because:

* It had no crashes.
* It produced longer answers.
* It made more tool calls.
* A model judge preferred its style.
* It received more positive feedback without controlling for task differences.

---

# 53. Evaluation thresholds

```typescript id="ri8yga"
export interface EvaluationThreshold {
  metricId: string;

  operator:
    | "greater_than"
    | "greater_or_equal"
    | "less_than"
    | "less_or_equal"
    | "equal";

  value: number;

  severity:
    | "informational"
    | "warning"
    | "blocking"
    | "critical";

  minimumSampleSize?: number;
}
```

## 53.1 Threshold categories

### Invariants

Must always pass:

```text id="bh26un"
Output schema validity
Authorization enforcement
Approval binding
Effect verification
Tenant isolation
No fabricated evidence
```

### Quality gates

Must meet minimum score:

```text id="vpsf3u"
Selection precision
Selection recall
Domain accuracy
Evidence coverage
Recovery success
```

### Guardrails

Must not regress materially:

```text id="658ckd"
Latency
Cost
Model calls
Provider calls
User corrections
Incident rate
```

---

# 54. Publication quality gate

```typescript id="gld4es"
export interface PublicationQualityGate {
  targetRevisionId: string;

  requiredSuites: string[];

  invariantResults: Array<{
    metric: string;
    passed: boolean;
  }>;

  qualityResults: Array<{
    metric: string;
    value: number;
    threshold: number;
    passed: boolean;
  }>;

  unresolvedIssues: EvaluationIssue[];

  decision:
    | "pass"
    | "conditional_pass"
    | "fail";

  reportHash: string;
}
```

A conditional pass should be prohibited for unresolved critical or safety failures.

---

# 55. Tool-type evaluation profiles

## 55.1 Deterministic computation

Examples:

* Calculator
* Unit conversion
* Formula evaluator

Priorities:

```text id="7q2gmv"
Exact accuracy
Property-based testing
Numerical stability
Input bounds
Resource limits
No model use
```

## 55.2 External retrieval

Examples:

* Web search
* arXiv search
* Weather
* Market data

Priorities:

```text id="m52bzc"
Freshness
Coverage
Provenance
Identifier validity
Provider failures
Partial results
Rate limits
```

## 55.3 Transformation

Examples:

* File conversion
* Data normalization
* Document extraction

Priorities:

```text id="anmg2e"
Losslessness
Schema conformance
Formatting
Encoding
Large inputs
Malicious files
```

## 55.4 Analysis

Examples:

* Financial ratios
* Portfolio risk
* Organisational comparison

Priorities:

```text id="jng8gk"
Calculation correctness
Assumption visibility
Source quality
Reproducibility
Scenario handling
Materiality
```

## 55.5 Code execution

Examples:

* Tests
* Compiler
* Static analysis

Priorities:

```text id="bqjcw8"
Sandbox integrity
Exit status
Log completeness
Resource limits
Network restrictions
Artifact correctness
```

## 55.6 External action

Examples:

* Email
* Task creation
* Calendar update

Priorities:

```text id="rmotvw"
Approval
Idempotency
Target correctness
Effect receipt
Reconciliation
Rollback
```

## 55.7 Agent-backed analysis

Examples:

* Research investigation
* Software diagnosis
* Organisational analysis

Priorities:

```text id="2zu5df"
Planning
Tool composition
Evidence faithfulness
Stopping
Cost
Model variability
Robustness
```

---

# 56. Domain evaluation examples

## 56.1 Web development

Tools:

```text id="qb011q"
web.capture_screenshot
web.inspect_dom
web.run_accessibility_audit
web.compare_visuals
web.run_frontend_tests
```

Evaluation dimensions:

* Correct page and viewport
* DOM extraction completeness
* Accessibility rule coverage
* Visual-difference accuracy
* False positive rate
* Test isolation
* Browser compatibility
* Artifact retention

## 56.2 Financial analysis

Tools:

```text id="o7wd90"
finance.retrieve_market_data
finance.normalize_statements
finance.calculate_var
finance.run_stress_scenario
```

Evaluation dimensions:

* Timestamp and source correctness
* Corporate-action handling
* Currency normalization
* Formula correctness
* Reconciliation to reference system
* Scenario reproducibility
* Numerical tolerances
* Missing-data disclosure

## 56.3 Software engineering

Tools:

```text id="9stta7"
software.search_repository
software.run_tests
software.inspect_logs
software.investigate_failure
```

Evaluation dimensions:

* Relevant-code retrieval
* Test reproducibility
* Log-event attribution
* Root-cause accuracy
* Patch-test success
* Unnecessary code changes
* Sandbox safety
* Repository effect boundaries

## 56.4 Research and learning

Tools:

```text id="k6e6lu"
research.search_papers
research.retrieve_paper
research.validate_citation
learning.generate_assessment
```

Evaluation dimensions:

* Search relevance
* Source diversity
* Identifier validity
* Citation support
* Concept coverage
* Difficulty calibration
* Answer-key correctness
* Learning progression

## 56.5 Project management

Tools:

```text id="4zgc4w"
project.create_task
project.update_milestone
project.assess_delivery_risk
```

Evaluation dimensions:

* Correct project
* Correct assignee
* Idempotency
* Dependency representation
* Deadline consistency
* Risk evidence
* Effect verification
* Approval compliance

## 56.6 Organisational effectiveness

Tools:

```text id="o8h6fh"
organisation.compare_units
organisation.analyse_workloads
organisation.map_process
organisation.benchmark_performance
```

Evaluation dimensions:

* Data comparability
* Population coverage
* Normalization
* Confounders
* Assumption transparency
* Fairness
* Actionability
* Unsupported management conclusions

---

# 57. Counterfactual evaluation

ServiceFabric should sometimes compare the selected action with plausible alternatives.

```typescript id="g3pft3"
export interface CounterfactualEvaluation {
  objectiveClass: string;

  selectedToolId?: string;
  alternativeToolIds: string[];

  selectedOutcomeScore: number;
  alternativeOutcomeScores: Record<string, number>;

  selectedCostUsd: number;
  alternativeCostEstimates: Record<string, number>;

  conclusion:
    | "selection_optimal"
    | "selection_acceptable"
    | "better_alternative_available"
    | "no_tool_would_be_better";
}
```

This helps identify:

* Overuse of agent-backed tools
* Tool catalogue confusion
* Cases where a primitive tool is sufficient
* Cases where a composite tool would improve outcomes
* Cases where no tool should have been used

---

# 58. Maintainability evaluation

A tool can function correctly but be operationally expensive.

Measure:

```text id="o2am74"
Maintenance interventions per 1,000 calls
Retries per successful call
Fallback rate
Provider-switch rate
Incident rate
Schema-drift frequency
Manual-review burden
Mean time to diagnosis
Mean time to recovery
```

High maintenance complexity may trigger evolution even when user-visible quality remains acceptable.

---

# 59. Observability privacy

Telemetry should follow data minimization.

```typescript id="3x7kfw"
export interface TelemetryDataPolicy {
  arguments:
    | "none"
    | "hash_only"
    | "classified_fields"
    | "encrypted_reference";

  results:
    | "none"
    | "metadata_only"
    | "classified_fields"
    | "encrypted_reference";

  modelContent:
    | "none"
    | "token_counts_only"
    | "redacted_sample"
    | "encrypted_reference";

  retention: {
    traces: string;
    metrics: string;
    logs: string;
    evaluations: string;
    audit: string;
  };

  permittedRegions: string[];
}
```

## 59.1 Default rules

* Do not log full prompts and responses by default.
* Do not place secrets in telemetry.
* Hash material arguments.
* Use opaque evidence references.
* Separate audit evidence from operational logs.
* Sample ordinary successful traces.
* Retain critical incidents fully under protected access.
* Apply tenant isolation.
* Redact personal and financial data.

---

# 60. Sampling

```typescript id="j1xpnf"
export interface TelemetrySamplingPolicy {
  baselineTraceSampleRate: number;

  alwaysSampleWhen:
    | Array<
        | "error"
        | "partial"
        | "uncertain_effect"
        | "security_event"
        | "approval_failure"
        | "canary"
        | "quarantine"
        | "schema_violation"
      >;

  highRiskSampleRate: number;

  maximumSamplesPerTenantPerHour?: number;
}
```

Recommended approach:

```text id="tpcapn"
Head sampling
    Basic volume control at invocation start.

Tail sampling
    Preserve traces based on outcome:
        errors
        high latency
        unusual cost
        retries
        security events
        uncertain effects
```

---

# 61. Telemetry integrity

Telemetry used for security, publication or effect verification must be protected from tampering.

Controls:

* Signed critical events
* Immutable audit store
* Append-only effect ledger
* Clock synchronization
* Stable revision identities
* Restricted write access
* Trace-to-audit linkage
* Data-loss alerting
* Collector authentication

Ordinary debug telemetry may be lossy. Governance evidence must not be.

---

# 62. Evaluation reproducibility

Every evaluation report should identify:

```typescript id="hnmgas"
export interface EvaluationReproducibility {
  suiteId: string;
  suiteVersion: string;
  datasetId: string;
  datasetVersion: string;

  targetRevisionId: string;

  modelConfigurationIds: string[];
  providerFixtureVersions: string[];

  policyBundleHash: string;
  environmentHash: string;

  randomSeeds: string[];

  executedAt: string;

  replayCommandRef?: string;
}
```

For non-deterministic tools, reproducibility means being able to recreate:

* Configuration
* Inputs
* Provider fixtures where available
* Sampling parameters
* Evaluation method
* Statistical result

It does not imply identical generated text.

---

# 63. Evaluation drift

Evaluation systems themselves can become stale.

Monitor:

* Benchmark saturation
* Overfitting
* New caller patterns
* New tool confusion
* Model changes
* Provider changes
* Domain changes
* Reviewer drift
* Data leakage
* Adversarial adaptation

```typescript id="18suyt"
export interface EvaluationSuiteStatus {
  suiteId: string;
  suiteVersion: string;

  state:
    | "current"
    | "aging"
    | "stale"
    | "compromised";

  lastReviewedAt: string;

  observedCoverageGaps: string[];

  replacementSuiteId?: string;
}
```

---

# 64. Human-review calibration

Human evaluators should receive:

* Rubric
* Examples
* Counterexamples
* Materiality guidance
* Blind candidate identifiers
* Conflict-resolution process

Measure:

```text id="wve4w5"
Inter-rater agreement
Reviewer variance
Reviewer reversal rate
Escalation rate
Time per review
```

A low-agreement dimension may require:

* Better rubric
* Narrower task definition
* Multiple reviewers
* Explicit uncertainty
* Reduced automation

---

# 65. Evaluation report

```typescript id="6d0o63"
export interface EvaluationReport {
  reportId: string;

  targetType: string;
  targetId: string;
  targetRevisionId: string;

  suiteResults: Array<{
    suiteId: string;
    suiteVersion: string;

    passedCases: number;
    failedCases: number;
    skippedCases: number;

    metrics: Record<string, number>;

    blockingFailures: EvaluationIssue[];
  }>;

  aggregateQuality: ToolQualityVector;

  invariantsPassed: boolean;
  publicationThresholdsPassed: boolean;

  recommendation:
    | "publish"
    | "publish_with_monitoring"
    | "repair"
    | "reject"
    | "quarantine";

  generatedAt: string;
  reportHash: string;
}
```

---

# 66. Evaluation issues

```typescript id="vyjelg"
export interface EvaluationIssue {
  issueCode: string;

  category: EvaluationCategory;

  severity:
    | "informational"
    | "warning"
    | "blocking"
    | "critical";

  caseId?: string;

  message: string;

  traceId?: string;
  evidenceRefs: string[];

  likelyRootCause:
    | "description"
    | "schema"
    | "implementation"
    | "maintenance"
    | "provider"
    | "model"
    | "policy"
    | "graph"
    | "evaluation";

  suggestedRepairStage?: string;
}
```

---

# 67. Evolution signals

Evaluation failures should produce structured evolution signals when they indicate design change rather than transient operations.

```text id="e4b426"
Repeated selection failure
    → description or boundary evolution

Repeated argument error
    → schema evolution

Evidence-quality decline
    → provider or verification evolution

Increasing retries
    → maintenance evolution

Cost per success increase
    → architecture or provider evolution

Recurring three-tool sequence
    → composite-tool evaluation
```

---

# 68. Tool Registry quality integration

The registry may consume:

```text id="12e4i3"
Domain quality
Agent-selection success
Reliability
Latency
Cost
Evidence coverage
Incident rate
Deprecation state
```

It must not use a quality metric that:

* Violates caller policy
* Averages away safety defects
* Is based on insufficient samples
* Leaks tenant data
* Creates circular popularity bias

Registry ranking should use confidence intervals or minimum-sample rules where practical.

---

# 69. Telemetry collector architecture

```text id="n725yl"
Tool and graph runtimes
        ↓ OTLP
Regional OpenTelemetry Collectors
        ↓
Processing:
    redaction
    tenant tagging
    sampling
    schema validation
    routing
        ↓
Destinations:
    trace store
    metric store
    log store
    security audit store
    evaluation event bus
    cost ledger
```

OpenTelemetry provides a collector-oriented architecture for processing and exporting observability signals; ServiceFabric should use collectors as the policy boundary for redaction, routing and sampling rather than having each capsule directly integrate with a specific monitoring vendor.

---

# 70. Telemetry processing pipeline

```text id="hrk3ti"
Receive
  ↓
Authenticate source
  ↓
Validate semantic schema
  ↓
Attach trusted resource metadata
  ↓
Redact prohibited attributes
  ↓
Apply tenant routing
  ↓
Apply sampling
  ↓
Calculate derived metrics
  ↓
Export
```

Tool-provided telemetry must not be trusted to assign:

* Tenant
* Authorization result
* Approval state
* Tool revision
* Security severity

These values should be attached or verified by platform enforcement points.

---

# 71. Evaluation runner topology

```text id="avjf5u"
Evaluation scheduler
        ↓
Evaluation suite registry
        ↓
Environment provisioner
        ↓
Target revision
        ↓
Fixtures and simulators
        ↓
Execution recorder
        ↓
Scorers
        ├── deterministic
        ├── reference
        ├── statistical
        ├── model judge
        └── human review
        ↓
Evaluation report
        ↓
Building / maintenance / evolution gate
```

---

# 72. Evaluation execution isolation

Evaluation runs should be isolated from production effects.

Controls:

* Test tenant
* Sandbox provider
* Synthetic accounts
* Read-only production replicas
* Fake communication endpoints
* Transaction simulators
* Ephemeral repositories
* Dedicated cost budget
* No production secrets unless explicitly required
* Automatic cleanup

High-risk evaluations must not rely on a prompt telling the agent not to commit effects. The environment must technically prevent them.

---

# 73. Declarative telemetry policy

```yaml id="qshpbv"
apiVersion: servicefabric.ai/v1alpha1
kind: TelemetryPolicy

metadata:
  id: standard-tool-telemetry
  version: 1.0.0

spec:
  signals:
    traces:
      enabled: true
      baselineSampleRate: 0.10

      alwaysSample:
        - error
        - partial
        - uncertain_effect
        - security_event
        - canary
        - schema_violation

    metrics:
      enabled: true

    logs:
      enabled: true
      arguments: hash_only
      results: metadata_only

    profiles:
      enabledFor:
        - command_runner
        - high_cpu_computation

  propagation:
    traceContext: true

    baggageAllowlist:
      - servicefabric.root_graph_run_id
      - servicefabric.graph_run_id
      - servicefabric.tool_invocation_id
      - servicefabric.tool_id
      - servicefabric.tool_revision_id
      - servicefabric.environment
      - servicefabric.experiment_id

  privacy:
    secretsPermitted: false
    rawPromptsPermitted: false
    rawResultsPermitted: false

  retention:
    traces: P30D
    logs: P30D
    metrics: P395D
    evaluations: P730D
    securityAudit: P2555D
```

Retention periods are deployment policy choices rather than universal defaults.

---

# 74. Declarative evaluation suite

```yaml id="jgqsyi"
apiVersion: servicefabric.ai/v1alpha1
kind: EvaluationSuite

metadata:
  id: research-search-agent-callability
  version: 1.0.0

spec:
  target:
    type: tool
    id: research.search_papers

  categories:
    - selection
    - negative_selection
    - arguments
    - interpretation
    - recovery
    - evidence
    - security

  datasets:
    - research-search-development
    - research-search-holdout
    - research-search-adversarial

  scorers:
    deterministic:
      - schema-conformance
      - identifier-validity
      - provenance-coverage
      - error-conformance

    modelJudge:
      - search-relevance
      - query-interpretation

    human:
      sampleRate: 0.05
      dimensions:
        - relevance
        - evidence-appropriateness

  thresholds:
    - metric: selection_precision
      operator: greater_or_equal
      value: 0.95
      severity: blocking

    - metric: selection_recall
      operator: greater_or_equal
      value: 0.95
      severity: blocking

    - metric: output_schema_validity
      operator: equal
      value: 1.0
      severity: critical

    - metric: provenance_coverage
      operator: equal
      value: 1.0
      severity: critical

    - metric: fabricated_citation_rate
      operator: equal
      value: 0
      severity: critical
```

---

# 75. Building-graph integration

The System-Building Graph must:

```text id="slmpj4"
Generate evaluation suites
      ↓
Run unit and contract evaluations
      ↓
Run agent-callability evaluations
      ↓
Run security evaluations
      ↓
Produce EvaluationReport
      ↓
Apply PublicationQualityGate
```

A ToolRevision cannot be published when:

* Critical invariant fails.
* Output schema validity is below 100%.
* Required agent-callability suite fails.
* Effect verification is incomplete.
* Evaluation evidence is missing.
* Evaluation suite is stale or compromised.

---

# 76. Maintenance-graph integration

The System-Maintenance Graph consumes online telemetry to:

* Update `ToolStatus`
* Open circuits
* Apply degradation
* Create incidents
* Quarantine
* Increase evaluation sampling
* Emit evolution signals

```text id="mr3rka"
Telemetry window
      ↓
Threshold and anomaly evaluation
      ↓
Operational interpretation
      ├── healthy
      ├── degraded
      ├── unavailable
      ├── suspicious
      └── unsafe
```

A statistical anomaly alone should not automatically quarantine a tool unless it corresponds to a safety invariant. It may trigger a health probe or evaluation.

---

# 77. Evolution-graph integration

The System-Evolution Graph uses:

* Baseline evaluation reports
* Historical traces
* Incident-derived cases
* Cost records
* Tool-confusion matrices
* Agent-recovery metrics
* Provider quality
* Canary reports

Candidate and baseline must run comparable suites.

```text id="7uej8e"
Baseline revision
    + fixed evaluation suite

Candidate revision
    + same evaluation suite

        ↓
Comparative evaluation
        ↓
Shadow
        ↓
Canary
        ↓
Promotion decision
```

---

# 78. Reference evaluation: `math.calculate`

## Required cases

```text id="8o0nj9"
Arithmetic
Operator precedence
Scientific notation
Boundary values
Invalid syntax
Division by zero
Complexity limit
Cancellation
No-network assertion
No-code-execution assertion
```

## Metrics

```text id="uh8xq6"
Exact result accuracy = 100%
Output schema validity = 100%
Unsafe expression execution = 0
p95 latency within target
Model calls = 0
Network calls = 0
```

## Agent-callability

* Select for exact arithmetic.
* Do not select for market-price retrieval.
* Do not select for symbolic mathematical proof unless supported.
* Construct a bounded expression.
* Interpret domain errors correctly.

---

# 79. Reference evaluation: `research.search_papers`

## Required cases

```text id="jcvwh7"
Direct scholarly search
General web-search negative case
Known-paper retrieval negative case
Quotation-verification negative case
Date filtering
Provider timeout
Duplicate results
Malformed DOI
Empty result
Partial provider success
Prompt injection in abstract
Conflicting metadata
```

## Metrics

```text id="dycyot"
Selection precision
Selection recall
Relevant-result rate
DOI validity
arXiv identifier validity
Provenance coverage
Duplicate rate
Partial-result interpretation
Provider fallback success
Cost per useful result
```

## Critical failures

```text id="l7cvdm"
Fabricated citation
Unsupported identifier
Missing provenance
External content altering policy
Output schema violation
```

---

# 80. Reference evaluation: `project.create_task`

## Required cases

```text id="o8wbi6"
Authorized project
Unauthorized project
Missing approval
Expired approval
Modified arguments after approval
Duplicate idempotency key
Provider timeout before commit
Provider timeout after commit
Task read-back verification
Incorrect assignee
Closed project
```

## Metrics

```text id="cx7y0n"
Effect verification rate = 100%
Duplicate task rate = 0
Approval binding rate = 100%
Target correctness = 100%
Uncertain-effect reconciliation rate
p95 execution latency
```

Any task created outside its approved target is a critical failure.

---

# 81. Reference graph evaluation: financial research

```text id="0auvrh"
Objective:
    Analyse liquidity and concentration risk for portfolio A.

Expected graph:
    retrieve authorized positions
    retrieve current market data
    validate timestamps
    calculate measures
    perform scenario analysis
    generate evidence-linked report

Prohibited:
    submit transaction
    modify portfolio
    use unauthorized account
    omit stale-data warning
```

Metrics:

```text id="l8nroq"
Graph completion
Calculation correctness
Evidence coverage
Tool-call efficiency
Stale-data recognition
No unauthorized effects
Report claim faithfulness
Cost per completed analysis
```

---

# 82. Dashboard views

ServiceFabric should provide several operational views.

## 82.1 Tool owner dashboard

* Availability
* Latency
* Errors
* Quality vector
* Invalid calls
* Provider health
* Cost
* Incidents
* Evolution signals

## 82.2 Agent engineer dashboard

* Selection confusion
* Argument validity
* Tool-call sequence
* Graph loops
* Recovery
* Model calls
* Token usage
* Tool catalogue size

## 82.3 Security dashboard

* Policy denials
* Approval failures
* Injection attempts
* Cross-tenant denials
* Secret-access failures
* Uncertain effects
* Quarantines

## 82.4 Domain owner dashboard

* Objective completion
* Domain accuracy
* Evidence quality
* User corrections
* Business outcomes
* Cost per completed workflow

## 82.5 Evolution dashboard

* Baseline versus candidate
* Shadow results
* Canary results
* Migration adoption
* Trigger recurrence
* Post-promotion regression

---

# 83. Alerts

Alerts should correspond to actionable conditions.

## Immediate alerts

```text id="yeqs4v"
Unauthorized effect
Cross-tenant exposure
Secret leakage
Output schema violation in effectful tool
Effect receipt forgery
Critical evaluation failure
Sandbox escape
```

## Rapid investigation

```text id="yfp0io"
Significant success-rate decline
Evidence coverage decline
High uncertain-effect rate
Provider schema drift
Tool-selection collapse
Cost amplification
Unexpected model-call growth
```

## Trend review

```text id="yu2d41"
Rising invalid arguments
Increasing fallback rate
Increasing maintenance intervention
Gradual latency regression
Tool confusion
Declining registry precision
```

Alert thresholds should avoid paging operators for ordinary recoverable tool errors.

---

# 84. Telemetry and evaluation APIs

Recommended internal capabilities:

```text id="scm5v8"
telemetry.start_trace
telemetry.record_event
telemetry.record_metric
telemetry.query_trace
telemetry.query_tool_metrics
telemetry.query_graph_metrics

evaluations.create_suite
evaluations.register_case
evaluations.run_suite
evaluations.compare_revisions
evaluations.run_historical_replay
evaluations.start_shadow
evaluations.score_run
evaluations.get_report

quality.get_tool_vector
quality.get_graph_vector
quality.report_user_feedback
quality.create_regression_case

cost.get_invocation_cost
cost.get_graph_cost
cost.get_objective_cost
```

Agent-facing access should ordinarily be read-only and limited to summarized operational information.

---

# 85. Telemetry service objectives

Illustrative platform objectives:

```yaml id="crwdsi"
tracePropagationRate: 0.9999
criticalAuditRecordRate: 1.0
effectTraceLinkageRate: 1.0

telemetryIngestionP95: PT10S
metricAvailabilityP95: PT1M
criticalSecurityEventAvailabilityP95: PT5S

evaluationReproducibilityRate: 1.0
publicationGateExecutionRate: 1.0

outputSchemaValidityRate: 1.0
effectVerificationTelemetryRate: 1.0
```

Ordinary sampled traces may be lost without compromising execution. Critical governance evidence may not.

---

# 86. Framework invariants

```text id="8zo9a7"
SF-Q001  Every graph run has a root trace.
SF-Q002  Every tool invocation links to its graph and revision.
SF-Q003  Every provider and model call links to its invocation.
SF-Q004  Every effect receipt links to the responsible invocation.
SF-Q005  Every evaluation result links to reproducible artifacts.
SF-Q006  Tool telemetry uses stable semantic attributes.
SF-Q007  Metric labels use bounded cardinality.
SF-Q008  Secrets are never stored in telemetry.
SF-Q009  Raw prompts and results are not logged by default.
SF-Q010  Tenant-sensitive telemetry remains tenant-isolated.
SF-Q011  Tool success requires contract-valid output.
SF-Q012  Provider success does not imply tool success.
SF-Q013  Protocol and tool-execution errors remain separate.
SF-Q014  Every native tool has an agent-callability suite.
SF-Q015  Every public tool has positive and negative selection cases.
SF-Q016  Schema-valid arguments are also evaluated semantically.
SF-Q017  Partial results receive interpretation tests.
SF-Q018  Effectful tools receive controlled effect tests.
SF-Q019  Every material incident produces a regression case.
SF-Q020  Every candidate is compared against a baseline.
SF-Q021  Shadow candidates cannot commit effects.
SF-Q022  Canary experiments have deterministic stopping rules.
SF-Q023  Safety invariants cannot be averaged into quality scores.
SF-Q024  Model judges cannot authorize actions.
SF-Q025  Model judges cannot verify effects as sole evidence.
SF-Q026  Evaluation datasets are versioned.
SF-Q027  Holdout cases remain inaccessible to generation agents.
SF-Q028  Evaluation suites are themselves monitored for drift.
SF-Q029  Cost is attributed to a user or system objective.
SF-Q030  Efficiency metrics cannot reward omitted safety controls.
SF-Q031  Registry ranking uses only sufficiently supported quality data.
SF-Q032  Telemetry failures do not disable governance enforcement.
SF-Q033  Critical audit evidence is integrity-protected.
SF-Q034  Evaluation failures emit structured issue codes.
SF-Q035  Repeated validated failures may emit evolution signals.
SF-Q036  Every publication decision includes an EvaluationReport hash.
SF-Q037  Every promoted candidate retains its comparative report.
SF-Q038  Every retired revision retains historical evaluation records.
SF-Q039  Human-review rubrics are versioned.
SF-Q040  ServiceFabric measures objective outcomes, not only tool activity.
```

---

# 87. Architectural decision

ServiceFabric should implement observability through two linked systems:

```text id="peguuk"
Operational telemetry
    Traces, metrics, logs and profiles

Semantic evaluation
    Cases, observations, scores and reports
```

They connect through shared identities:

```text id="39cyhz"
ToolRevision
GraphRevision
TraceId
GraphRunId
ToolInvocationId
EvaluationRunId
ExperimentId
IncidentId
```

The full feedback path becomes:

```text id="b99c3y"
Tool or graph executes
        ↓
OpenTelemetry signals record behaviour
        ↓
Evaluation system determines semantic quality
        ↓
Maintenance system updates health
        ↓
Registry adjusts discovery and routing
        ↓
Evolution system diagnoses persistent gaps
        ↓
Building system creates the next revision
```

The central ServiceFabric quality rule is:

> A tool is production-ready only when it is operationally reliable, contract-valid, correctly selectable, semantically useful, evidence-grounded, safely governed, and economically observable.

This prevents a tool from being considered successful merely because it returned a response or because a language model chose to call it.
