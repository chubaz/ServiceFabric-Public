# ServiceFabric System-Evolution Graph Specification v1

**Status:** Architecture baseline
**Graph family:** `system-evolution`
**Default graph:** `standard-tool-evolution`
**API version:** `servicefabric.ai/v1alpha1`
**Primary output:** New `ToolDefinition` and immutable `ToolRevision`

---

# 1. Purpose

The **System-Evolution Graph** improves, expands, restructures, deprecates, or retires ServiceFabric tools in response to evidence.

```text
Operational evidence
        ↓
Evolution qualification
        ↓
Root-cause analysis
        ↓
Change and compatibility classification
        ↓
Candidate design
        ↓
Controlled construction
        ↓
Evaluation and experimentation
        ↓
Canary deployment
        ↓
Promotion, migration, rollback, or rejection
```

The graph converts observed needs into controlled architectural change.

It must determine:

* Whether a tool genuinely needs to change
* Whether the problem belongs to the implementation, contract, maintenance graph, provider, policy, or tool boundary
* Whether the change is backward-compatible
* Whether an existing tool should be expanded, split, merged, deprecated, or retired
* Whether a recurring graph composition should become a composite tool
* Whether the candidate performs better than the active revision
* Whether callers require migration
* Whether the old revision can be retired safely

---

# 2. MCP evolution baseline

As of **July 11, 2026**, the official MCP specification site identifies `2025-11-25` as the latest released specification. A `2026-07-28` revision exists as a release candidate and draft, but should not yet replace the released production profile.

ServiceFabric should therefore maintain two MCP compatibility lanes:

```text
Production lane
    MCP 2025-11-25
    Required for active production tools

Preview lane
    MCP 2026-07-28 release candidate
    Permitted for compatibility experiments only
```

A protocol evolution must not automatically alter a tool’s domain contract.

```text
Canonical ToolDefinition
        ↓
MCP 2025-11-25 projection
        ├── active production projection
        │
        └── MCP preview projection
              used for conformance experiments
```

This allows ServiceFabric to prepare for future protocol changes without coupling tool evolution to an unreleased specification.

---

# 3. Core principle: revisions are replaced, not mutated

A published `ToolRevision` is immutable.

```text
ToolRevision 1.2.3
      │
      ├── observed evidence
      ├── diagnosed shortcomings
      └── evolution proposal
                ↓
        ToolDefinition 1.3.0
                ↓
        ToolRevision 1.3.0
```

The system-evolution graph never edits revision `1.2.3`.

It creates:

* A new definition version
* A new implementation artifact
* A new maintenance graph version where necessary
* A new policy bundle where necessary
* A new MCP projection
* New evaluations
* A new immutable revision

This preserves:

* Auditability
* Reproducibility
* Rollback
* Contract history
* Comparison between revisions
* Approval integrity

---

# 4. Responsibilities

The system-evolution graph performs six classes of work.

## 4.1 Evidence management

* Receive evolution signals
* Aggregate related signals
* Validate evidence
* Remove duplicates
* Determine severity
* Establish affected populations

## 4.2 Diagnosis

* Reproduce the observed problem
* Identify root cause
* Distinguish design defects from operational incidents
* Determine whether the problem is local or systemic
* Identify affected revisions, providers, callers, and graphs

## 4.3 Change design

* Classify the required change
* Select version impact
* Design candidate behaviour
* Design migration
* Design experiments
* Update agentic backing where justified

## 4.4 Candidate construction

* Invoke the system-building graph
* Generate new artifacts
* Run security and governance checks
* Produce a deployment candidate

## 4.5 Controlled validation

* Historical replay
* Offline evaluations
* Shadow execution
* A/B or champion–challenger testing
* Canary release
* Policy and side-effect verification

## 4.6 Lifecycle management

* Promote a candidate
* Roll back a failed candidate
* Deprecate earlier versions
* Migrate callers
* Retire unused versions
* Preserve historical records

---

# 5. Non-responsibilities

The evolution graph does not:

* Repair an individual production call
* Retry a provider failure during an invocation
* Modify runtime health state directly
* Bypass the system-building graph
* Publish code without evaluation
* Alter authorization merely to improve adoption
* Change a tool contract silently
* Force migration without compatibility analysis
* Retire a tool while active callers still depend on it
* Treat every operational incident as a design problem

Those responsibilities remain separated:

```text
Maintenance graph
    Handles live calls, incidents and health

Evolution graph
    Designs replacement behaviour

Building graph
    Constructs and verifies the replacement

Deployment controller
    Manages rollout and traffic

Registry
    Manages versions and lifecycle visibility
```

---

# 6. Evolution inputs

The graph accepts an `EvolutionRequest`.

```typescript
export interface EvolutionRequest {
  requestId: string;

  toolId: string;
  baselineRevisionId?: string;

  trigger:
    | EvolutionSignal
    | ManualEvolutionRequest
    | ProtocolEvolutionRequest
    | DependencyEvolutionRequest;

  requestedBy: {
    principalId: string;
    type: "system" | "owner" | "operator" | "developer";
  };

  constraints?: {
    maximumRiskIncrease?: "none" | "low" | "medium";
    preserveBackwardCompatibility?: boolean;
    targetReleaseDate?: string;
    maximumExperimentCostUsd?: number;
    prohibitedProviders?: string[];
  };

  requestedAt: string;
}
```

## 6.1 Evolution signals

Signals may originate from:

* Invocation maintenance
* Operational maintenance
* Evaluation suites
* Tool registry analytics
* External graph telemetry
* Incident records
* Security monitoring
* Provider change notices
* MCP compatibility testing
* Tool owners
* Domain owners
* Users

```typescript
export interface EvolutionSignal {
  signalId: string;

  toolId: string;
  revisionId?: string;

  type:
    | "repeated_invalid_calls"
    | "selection_confusion"
    | "quality_decline"
    | "latency_regression"
    | "cost_regression"
    | "provider_drift"
    | "security_defect"
    | "missing_capability"
    | "recurring_fallback"
    | "recurring_composition"
    | "maintenance_complexity"
    | "policy_mismatch"
    | "protocol_change"
    | "dependency_deprecation"
    | "manual_request";

  severity: "low" | "medium" | "high" | "critical";

  evidenceRefs: string[];

  observedWindow?: {
    from: string;
    to: string;
  };

  createdAt: string;
}
```

---

# 7. Evolution state

```typescript
export interface ToolEvolutionState {
  run: {
    evolutionRunId: string;
    requestId: string;
    graphVersion: string;
    currentNode: string;

    status:
      | "received"
      | "qualifying"
      | "diagnosing"
      | "designing"
      | "building"
      | "evaluating"
      | "experimenting"
      | "migrating"
      | "completed"
      | "rejected"
      | "rolled_back"
      | "failed";
  };

  baseline: {
    definition?: ToolDefinition;
    revision?: ResolvedToolRevision;
    deployment?: ToolDeployment;
    status?: ToolStatus;
    dependentCallers: DependentCaller[];
  };

  evidence: {
    signals: EvolutionSignal[];
    incidents: IncidentRecord[];
    invocationSamples: InvocationSample[];
    evaluationReports: EvaluationReport[];
    providerReports: ProviderEvolutionReport[];
  };

  diagnosis: {
    reproduction?: ReproductionReport;
    rootCause?: RootCauseAnalysis;
    affectedScope?: AffectedScope;
  };

  proposal: {
    changeClassification?: ChangeClassification;
    targetArchitecture?: EvolutionTarget;
    candidateDefinition?: ToolDefinition;
    compatibility?: CompatibilityReport;
    migrationPlan?: MigrationPlan;
    experimentPlan?: ExperimentPlan;
  };

  candidate: {
    buildRequestId?: string;
    revisionId?: string;
    reports?: CandidateReports;
  };

  rollout: {
    shadowReport?: ShadowEvaluationReport;
    canaryReport?: CanaryReport;
    migrationStatus?: MigrationStatus;
    promotionDecision?: PromotionDecision;
  };

  decisions: EvolutionDecisionRecord[];
  issues: EvolutionIssue[];
}
```

---

# 8. Evolution graph topology

```text
E00 START
  ↓
E01 Validate evolution request
  ↓
E02 Load baseline and dependency graph
  ↓
E03 Aggregate evidence
  ↓
E04 Qualify evolution need
  ├── INCIDENT_ONLY ───────────────→ RETURN_TO_MAINTENANCE
  ├── INSUFFICIENT_EVIDENCE ───────→ OBSERVE
  ├── DUPLICATE_REQUEST ───────────→ JOIN_EXISTING
  └── EVOLUTION_JUSTIFIED
  ↓
E05 Reproduce observed problem
  ├── NOT_REPRODUCIBLE ────────────→ OBSERVE
  └── REPRODUCED
  ↓
E06 Root-cause analysis
  ↓
E07 Determine affected scope
  ↓
E08 Select evolution target
  ├── CONFIGURATION_ONLY ──────────→ E12
  ├── PATCH_TOOL ──────────────────→ E09
  ├── EXTEND_TOOL ─────────────────→ E09
  ├── BREAKING_TOOL_CHANGE ────────→ E09
  ├── SPLIT_TOOL ──────────────────→ E09
  ├── MERGE_TOOLS ─────────────────→ E09
  ├── CREATE_COMPOSITE_TOOL ───────→ E09
  ├── CREATE_NEW_TOOL ─────────────→ E09
  ├── DEPRECATE_TOOL ──────────────→ E25
  └── RETIRE_TOOL ─────────────────→ E27
  ↓
E09 Design candidate behaviour
  ↓
E10 Compatibility and version analysis
  ↓
E11 Design migration and rollback
  ↓
E12 Design experiment
  ↓
E13 Review evolution proposal
  ├── CHANGES_REQUESTED ───────────→ E06/E09
  ├── REJECTED ────────────────────→ REJECT
  └── APPROVED
  ↓
E14 Invoke system-building graph
  ├── BUILD_FAILED ────────────────→ E09
  └── CANDIDATE_BUILT
  ↓
E15 Candidate verification
  ↓
E16 Historical replay
  ↓
E17 Offline comparative evaluation
  ├── REGRESSION ──────────────────→ E09/E14
  └── PASS
  ↓
E18 Shadow execution
  ├── REGRESSION ──────────────────→ E09/E14
  └── PASS
  ↓
E19 Canary readiness gate
  ↓
E20 Canary deployment
  ↓
E21 Canary observation
  ├── FAIL ────────────────────────→ E22
  ├── EXTEND_OBSERVATION ──────────→ E21
  └── PASS
  ↓
E22 Rollback and incident analysis
  ↓
E23 Promotion decision
  ├── REJECT_CANDIDATE ────────────→ REJECT
  ├── CONTINUE_CANARY ─────────────→ E21
  └── PROMOTE
  ↓
E24 Promote candidate revision
  ↓
E25 Deprecate superseded revision
  ↓
E26 Migrate callers
  ↓
E27 Retirement readiness
  ├── NOT_READY ───────────────────→ E26/OBSERVE
  └── READY
  ↓
E28 Retire superseded revision
  ↓
E29 Close evolution run
  ↓
END
```

---

# 9. E01–E04 — Qualification

## E01 — Validate request

**Node type:** Deterministic

Checks:

* Tool exists or was previously registered.
* Requester or system trigger is authorized.
* Signal evidence references are accessible.
* No incompatible evolution run already owns the same target.
* Critical incidents receive priority.
* Experiment and build budgets can be established.

## E02 — Load baseline

The graph loads:

* Active ToolDefinition
* Immutable ToolRevision
* Maintenance graph
* Policies
* Current and historical ToolStatus
* Active deployment
* Previous revisions
* Callers and dependent graphs
* Tool-selection relationships
* Provider dependencies
* Evaluation history
* Existing deprecation notices

## E03 — Aggregate evidence

Related signals are grouped by:

* Tool
* Revision
* Error or quality category
* Provider
* Caller type
* Time window
* Input pattern
* Graph composition pattern
* Environment
* Tenant, where permitted

```typescript
export interface EvolutionEvidenceCluster {
  clusterId: string;

  signalType: string;
  affectedToolId: string;
  affectedRevisions: string[];

  occurrenceCount: number;
  uniqueCallerCount: number;

  firstObservedAt: string;
  lastObservedAt: string;

  severityDistribution: Record<string, number>;
  evidenceRefs: string[];

  confidence: number;
}
```

## E04 — Qualify need

Possible outcomes:

```typescript
export type EvolutionQualification =
  | {
      outcome: "evolution_justified";
      rationaleCodes: string[];
    }
  | {
      outcome: "maintenance_only";
      rationaleCodes: string[];
    }
  | {
      outcome: "insufficient_evidence";
      observationPlan: ObservationPlan;
    }
  | {
      outcome: "duplicate";
      existingEvolutionRunId: string;
    }
  | {
      outcome: "invalid_signal";
      rationaleCodes: string[];
    };
```

### Maintenance-only examples

* Temporary provider outage
* Expired credential
* One malformed request
* Isolated network failure
* A circuit breaker operating correctly

### Evolution examples

* Repeated schema confusion
* Sustained quality decline
* Recurring provider incompatibility
* Excessive maintenance repairs
* Tool boundary causing unsafe composition
* New required capability
* Recurring three-tool sequence
* Security defect requiring implementation changes

---

# 10. E05 — Reproduction

An evolution should normally be based on reproducible behaviour.

```typescript
export interface ReproductionReport {
  reproduced: boolean;

  environment: string;
  baselineRevisionId: string;

  inputClasses: string[];
  invocationRefs: string[];

  expectedBehaviour: string;
  observedBehaviour: string;

  frequency: number;
  confidence: number;

  reproductionArtifacts: string[];
}
```

Reproduction methods include:

* Historical invocation replay
* Synthetic test cases
* Provider-response replay
* Contract fixtures
* Agent-selection replay
* Dependency emulation
* Security adversarial testing
* Controlled model re-execution

Sensitive production data should be transformed, redacted, or represented through approved fixtures before replay.

---

# 11. E06 — Root-cause analysis

**Node type:** Analysis agent plus deterministic evidence validation

```typescript
export interface RootCauseAnalysis {
  primaryCategory:
    | "description"
    | "input_schema"
    | "output_schema"
    | "implementation"
    | "maintenance_graph"
    | "provider"
    | "model"
    | "policy"
    | "tool_boundary"
    | "dependency"
    | "protocol_projection"
    | "caller_graph"
    | "operational_configuration";

  contributingCategories: string[];

  rootCauses: RootCause[];
  rejectedHypotheses: RootCauseHypothesis[];

  confidence: number;
  evidenceRefs: string[];
}
```

## 11.1 Diagnosis rules

The graph must distinguish:

```text
Symptom:
    Agents submit invalid date fields.

Possible causes:
    Poor field descriptions
    Excessive schema complexity
    Incorrect examples
    Caller-model regression
    Unsupported date format
```

It must not assume that invalid calls mean the implementation is defective.

Similarly:

```text
Symptom:
    Tool latency increased.

Possible causes:
    Provider degradation
    Maintenance retries
    Model-ranking overhead
    Larger payloads
    New caller behaviour
    Infrastructure regression
```

---

# 12. E07 — Affected scope

```typescript
export interface AffectedScope {
  revisions: string[];
  deployments: string[];
  environments: string[];

  providers: string[];
  callerTypes: string[];
  dependentGraphs: string[];

  estimatedAffectedInvocationRate: number;
  affectedEffectClasses: string[];

  dataMigrationRequired: boolean;
  callerMigrationRequired: boolean;
}
```

The graph should identify whether the issue affects:

* One provider
* One deployment
* One revision
* Every revision of the tool
* The tool boundary itself
* Several related tools
* The entire Tool Capsule framework

A platform-wide issue should be escalated into a platform-evolution process rather than patched independently in every capsule.

---

# 13. E08 — Evolution target selection

```typescript
export type EvolutionTarget =
  | {
      type: "configuration_change";
      target: string;
    }
  | {
      type: "patch_revision";
      toolId: string;
    }
  | {
      type: "minor_extension";
      toolId: string;
    }
  | {
      type: "major_revision";
      toolId: string;
    }
  | {
      type: "split_tool";
      sourceToolId: string;
      proposedToolIds: string[];
    }
  | {
      type: "merge_tools";
      sourceToolIds: string[];
      proposedToolId: string;
    }
  | {
      type: "composite_tool";
      componentToolIds: string[];
      proposedToolId: string;
    }
  | {
      type: "new_tool";
      proposedToolId: string;
    }
  | {
      type: "deprecate";
      toolId: string;
    }
  | {
      type: "retire";
      toolId: string;
    };
```

## 13.1 Configuration change

Appropriate when:

* No contract changes
* No code changes
* Existing allowed provider routing changes
* Threshold adjustment remains within approved policy
* Concurrency or scaling changes
* Feature flag changes already anticipated by the revision

A configuration change must still be versioned and auditable.

## 13.2 Patch revision

Appropriate for:

* Bug fix
* Internal performance improvement
* Provider adapter repair
* Prompt improvement preserving semantics
* Description clarification
* Maintenance logic correction
* Security fix without caller-visible contract change

## 13.3 Minor extension

Appropriate for:

* New optional input
* New optional output
* Additional provider
* New compatible filter
* Additional evidence metadata
* New declared fallback

## 13.4 Major revision

Required for:

* New required input
* Removed input or output
* Changed output meaning
* Changed side-effect class
* Statefulness change
* Authorization change
* Approval change
* Materially changed error semantics
* Incompatible freshness or quality guarantee

---

# 14. Tool-boundary evolution

## 14.1 Split

A tool should be split when:

* It combines unrelated objectives.
* It exposes several effect classes.
* Callers use only isolated subsets.
* Authorization differs by operation.
* Failures cannot be represented coherently.
* Agent selection is poor because the description is too broad.

Example:

```text
finance.manage_transaction
        ↓
finance.prepare_transaction
finance.validate_transaction
finance.submit_transaction
finance.get_transaction_status
```

## 14.2 Merge

Tools may be merged when:

* They are semantically indistinguishable to callers.
* Agents consistently confuse them.
* They differ only by provider.
* Their contracts can be unified without ambiguity.
* Separate exposure creates unnecessary tool-selection load.

Provider-specific implementations should normally remain hidden behind one public capability.

## 14.3 Composite tool

A new composite tool may be created when:

* A sequence recurs frequently.
* The sequence has one bounded outcome.
* Intermediate outputs are implementation details.
* The combined effects can be governed coherently.
* Centralized recovery materially improves reliability.

Example:

```text
research.search_papers
research.retrieve_metadata
research.validate_citations
        ↓
research.build_evidence_set
```

The composite should not replace the primitive tools unless their independent use is no longer valuable.

---

# 15. E09 — Candidate behaviour design

The graph creates a candidate `ToolDefinition`.

```typescript
export interface CandidateBehaviourDesign {
  baselineVersion: string;
  proposedVersion: string;

  changeSummary: string[];

  retainedSemantics: string[];
  addedSemantics: string[];
  removedSemantics: string[];
  changedSemantics: string[];

  interfaceChanges: InterfaceChange[];
  effectChanges: EffectChange[];
  policyChanges: PolicyChange[];

  maintenanceChanges: MaintenanceChange[];
  agenticBackingChanges: AgenticBackingChange[];

  expectedBenefits: ExpectedBenefit[];
  knownRisks: CandidateRisk[];
}
```

## 15.1 Minimal-change principle

The graph should prefer the smallest change that resolves the verified root cause without creating unnecessary capability expansion.

Bad response:

```text
Observed problem:
    One search provider changed its date format.

Proposed change:
    Replace the search tool with a fully autonomous research agent.
```

Appropriate response:

```text
Update provider mapping and add contract-drift tests.
```

---

# 16. Agentic-backing evolution

The graph may change the level of agentic backing, but only with explicit justification.

## 16.1 Increase in backing

Possible when:

* Deterministic routing cannot handle semantic ambiguity.
* Relevance ranking materially improves outcomes.
* Structured extraction is required from unstructured sources.
* Multi-step diagnosis is intrinsic to the capability.
* Evidence shows a bounded model-assisted process improves quality.

Required controls:

* Declared model purposes
* New budgets
* New data-classification analysis
* Model-failure fallback
* New adversarial tests
* Cost evaluation
* Human review

## 16.2 Reduction in backing

Prefer reducing model use when:

* Deterministic methods now perform adequately.
* Cost is disproportionate.
* Model variability causes regressions.
* A stable provider or domain algorithm replaces reasoning.
* The model is being used only for formatting.
* Latency is materially improved.

## 16.3 Agentic expansion anti-pattern

A tool must not become more autonomous merely because maintenance is difficult.

High maintenance complexity can indicate:

* A poor tool boundary
* An unstable provider
* An inadequate implementation
* An incorrect contract
* Excessive internal composition

---

# 17. E10 — Compatibility analysis

```typescript
export interface CompatibilityReport {
  classification:
    | "fully_compatible"
    | "backward_compatible"
    | "conditionally_compatible"
    | "breaking";

  inputCompatibility: CompatibilityDimension;
  outputCompatibility: CompatibilityDimension;
  errorCompatibility: CompatibilityDimension;
  effectCompatibility: CompatibilityDimension;
  authorizationCompatibility: CompatibilityDimension;
  operationalCompatibility: CompatibilityDimension;
  mcpCompatibility: CompatibilityDimension;

  affectedCallerPatterns: CallerCompatibilityImpact[];
  requiredMigrations: MigrationRequirement[];

  recommendedVersionChange:
    | "patch"
    | "minor"
    | "major";
}
```

## 17.1 Compatibility dimensions

### Input compatibility

* Are existing calls still valid?
* Have defaults changed?
* Have bounds narrowed?
* Has field meaning changed?

### Output compatibility

* Are existing required fields preserved?
* Has a value changed type?
* Has meaning changed despite the same type?
* Can old callers safely ignore new fields?

### Error compatibility

* Have stable error codes changed?
* Has retryability changed?
* Can callers still recover correctly?

### Effect compatibility

* Has a read become a write?
* Has reversibility changed?
* Has idempotency changed?
* Has external communication been introduced?

### Authorization compatibility

* Are new scopes required?
* Is approval newly required?
* Has tenant visibility changed?

### Operational compatibility

* Have latency, cost, freshness, or availability guarantees changed?

---

# 18. Semantic-version rules

```text
PATCH
    Caller-visible semantics preserved

MINOR
    Backward-compatible capability expansion

MAJOR
    Caller migration may be required
```

## 18.1 Patch examples

* Fix incorrect calculation
* Improve ranking prompt without changing output semantics
* Replace failing provider
* Clarify description
* Add internal retry protection

## 18.2 Minor examples

* Add optional date filter
* Add optional evidence field
* Add compatible provider
* Add a new partial-result warning

## 18.3 Major examples

* Make `accountId` required
* Replace numeric amount with a monetary object
* Change from delayed to real-time-only data
* Introduce persistent effects
* Require human approval
* Replace one tool with several split tools

A security fix may be behaviourally urgent but still require a major version when it changes caller-visible semantics.

---

# 19. E11 — Migration and rollback design

Every breaking change requires a migration plan before the candidate is built.

```typescript
export interface MigrationPlan {
  sourceToolId: string;
  sourceVersions: string[];

  targetTools: Array<{
    toolId: string;
    versionConstraint: string;
  }>;

  callerSegments: CallerMigrationSegment[];

  adapters: MigrationAdapter[];
  documentationRef?: string;

  deprecationStartAt?: string;
  migrationDeadline?: string;
  retirementEarliestAt?: string;

  rollback: RollbackPlan;

  completionCriteria: string[];
}
```

## 19.1 Caller segments

```typescript
export interface CallerMigrationSegment {
  segmentId: string;

  callerType:
    | "external_mcp_client"
    | "internal_graph"
    | "scheduled_workflow"
    | "human_user"
    | "third_party_integration";

  callerIds: string[];

  migrationMode:
    | "automatic"
    | "compatibility_adapter"
    | "owner_update"
    | "manual";

  status:
    | "not_started"
    | "in_progress"
    | "validated"
    | "blocked";
}
```

## 19.2 Compatibility adapters

Temporary adapters may:

* Rename fields
* Supply safe legacy defaults
* Transform old output shape
* Map old tool names
* Translate stable error codes

They may not:

* Fabricate missing required intent
* Bypass new approval
* Hide a new side effect
* Weaken authorization
* Convert an unsafe call automatically

Compatibility adapters must have an explicit retirement date.

---

# 20. E12 — Experiment design

```typescript
export interface ExperimentPlan {
  experimentId: string;

  hypothesis: string;

  baselineRevisionId: string;
  candidateRevisionId?: string;

  stages:
    | Array<
        | "offline_replay"
        | "benchmark"
        | "shadow"
        | "canary"
        | "controlled_ab"
      >;

  primaryMetrics: ExperimentMetric[];
  guardrailMetrics: ExperimentMetric[];

  sampleRequirements: {
    minimumInvocations: number;
    minimumDuration?: string;
    requiredCallerSegments: string[];
  };

  stoppingRules: StoppingRule[];

  dataPolicyRef: string;
  maximumCostUsd: number;
}
```

## 20.1 Hypothesis example

```text
Changing the scholarly-search routing policy to prefer Crossref for
DOI-focused queries will increase identifier validity from 96% to at
least 99%, without increasing p95 latency by more than 10%.
```

## 20.2 Primary metrics

Measure the intended benefit:

* Success rate
* Relevant-result rate
* Identifier validity
* Agent-selection accuracy
* Recovery success
* Cost per successful call
* Completion time

## 20.3 Guardrail metrics

Prevent hidden regressions:

* Authorization denials
* Output-schema validity
* Evidence coverage
* Side-effect errors
* p95 and p99 latency
* Cost
* Model calls
* Provider concentration
* User correction rate
* Incident rate

## 20.4 Stopping rules

Examples:

* Any unauthorized effect
* Any cross-tenant exposure
* Any fabricated effect receipt
* Output validity below 100%
* Error rate exceeds baseline by 5 percentage points
* Cost exceeds maximum
* Critical incident occurs
* Evidence coverage falls below threshold

---

# 21. E13 — Proposal review

The review package includes:

* Evidence summary
* Reproduction report
* Root-cause analysis
* Proposed target
* Compatibility report
* Version classification
* Candidate ToolDefinition
* Experiment plan
* Migration plan
* Rollback plan
* Risk change
* Agentic-backing change
* Expected benefits
* Known uncertainties

Required reviewers depend on the proposed change.

| Change                   | Reviewers                              |
| ------------------------ | -------------------------------------- |
| Description-only patch   | Tool owner                             |
| Implementation patch     | Technical owner                        |
| New provider             | Technical and security                 |
| Schema extension         | Technical and domain owner             |
| Breaking contract        | Technical, domain and caller owners    |
| New side effect          | Security, governance and domain        |
| Agentic-backing increase | AI engineering and security            |
| Financial effect change  | Finance control and governance         |
| Retirement               | Tool owner and dependent caller owners |

Review approval is bound to the proposal hash.

---

# 22. E14 — Building-graph invocation

The evolution graph does not construct production artifacts directly.

It prepares a new `ToolBuildRequest` and invokes the system-building graph.

```text
Evolution diagnosis
        ↓
Candidate ToolDefinition
        ↓
ToolBuildRequest
        ↓
System-Building Graph
        ↓
New immutable ToolRevision
```

```typescript
export interface EvolutionBuildRequest {
  source: {
    type: "evolution";
    evolutionRunId: string;
    baselineRevisionId: string;
  };

  proposedDefinition: ToolDefinition;

  compatibilityReportRef: string;
  migrationPlanRef?: string;
  experimentPlanRef: string;

  requiredRegressionSuites: string[];
  retainedHistoricalCases: string[];
}
```

The building graph must run all normal gates. Evolution status does not waive:

* Security verification
* Contract testing
* Agent-callability evaluation
* MCP conformance
* Review requirements
* Artifact signing

---

# 23. E15–E17 — Candidate verification

## 23.1 Baseline regression suite

The candidate must run:

* Current tool tests
* Historical failure cases
* Incident-derived cases
* Existing agent-callability cases
* Security cases
* Effect-verification cases
* Provider-drift cases
* MCP conformance tests

## 23.2 Historical replay

Historical replay compares the candidate against past invocations.

```typescript
export interface ReplayComparison {
  invocationClass: string;

  baselineOutcome: string;
  candidateOutcome: string;

  qualityDelta?: number;
  latencyDeltaMs?: number;
  costDeltaUsd?: number;

  contractCompatible: boolean;
  evidenceCompatible: boolean;
  effectCompatible: boolean;
}
```

Production requests should be replayed only under approved privacy controls.

Writes must be:

* Simulated
* Directed to a sandbox
* Replaced with recorded provider fixtures
* Blocked before commitment

## 23.3 Offline comparative evaluation

```text
Baseline revision
        ├── evaluation dataset
        └── historical replay

Candidate revision
        ├── same evaluation dataset
        └── same historical replay

              ↓
       Comparative report
```

A candidate should not be promoted merely because it passes independently. It must demonstrate that it resolves the target issue without unacceptable regression.

---

# 24. E18 — Shadow execution

In shadow mode, the active revision serves the caller while the candidate receives a copy of eligible calls.

```text
Caller invocation
      ↓
Active revision ─────────────→ caller result
      │
      └── redacted shadow copy
                 ↓
         Candidate revision
                 ↓
       comparative telemetry
```

## 24.1 Shadow restrictions

The candidate:

* Must not produce externally visible effects.
* Must not send messages.
* Must not create tasks.
* Must not submit transactions.
* Must not mutate production state.
* Must not consume unrestricted provider quotas.
* Must not expose results to the caller as authoritative.

For write tools, shadow mode should execute only:

* Planning
* Validation
* Action-preview generation
* Sandbox execution
* Recorded-provider simulation

## 24.2 Shadow comparison

Measure:

* Output agreement
* Quality improvement
* Error-class differences
* Provider selection
* Latency
* Cost
* Evidence coverage
* Model usage
* Tool-call count

---

# 25. E19–E21 — Canary rollout

## 25.1 Canary readiness gate

The candidate must have:

* Signed immutable revision
* Passing build report
* Passing security report
* Passing comparative evaluation
* Valid rollback target
* Active maintenance graph
* Incident owner
* Canary traffic policy
* Guardrail thresholds
* No unresolved critical defects

## 25.2 Canary traffic

Canary assignment may be based on:

* Percentage of eligible calls
* Internal callers only
* Specific tenant
* Specific graph
* Low-risk request class
* Read-only requests
* Selected provider
* Opt-in users

```typescript
export interface CanaryPolicy {
  candidateRevisionId: string;
  baselineRevisionId: string;

  eligibleCallerSegments: string[];
  eligibleEffectClasses: string[];

  initialTrafficPercentage: number;
  maximumTrafficPercentage: number;

  expansionSteps: number[];

  minimumObservationPerStep: string;
  guardrails: CanaryGuardrail[];
}
```

## 25.3 Risk-based rollout

Suggested profiles:

```text
Low-risk deterministic patch:
    5% → 25% → 100%

External retrieval change:
    1% → 10% → 50% → 100%

Reversible write:
    internal callers → 1% → 10% → 50% → 100%

Financial or irreversible effect:
    sandbox → supervised calls → restricted canary → manual promotion
```

Percentages are defaults, not substitutes for risk analysis.

---

# 26. Canary analysis

```typescript
export interface CanaryReport {
  baselineRevisionId: string;
  candidateRevisionId: string;

  observationWindow: {
    from: string;
    to: string;
  };

  invocationCounts: {
    baseline: number;
    candidate: number;
  };

  metricComparisons: MetricComparison[];
  incidents: string[];

  compatibilityDefects: CompatibilityDefect[];

  recommendation:
    | "promote"
    | "continue"
    | "reduce_traffic"
    | "rollback"
    | "reject";
}
```

## 26.1 Candidate success conditions

The candidate must:

* Resolve the qualifying issue.
* Meet all publication thresholds.
* Remain within latency and cost guardrails.
* Preserve output validity.
* Preserve or improve evidence coverage.
* Introduce no unauthorized effects.
* Satisfy compatibility commitments.
* Avoid unacceptable caller confusion.

## 26.2 Statistical and practical significance

Promotion should consider both:

* Whether an observed difference is unlikely to be random
* Whether the difference is operationally meaningful

A statistically detectable 1-millisecond latency gain may not justify added complexity. A small improvement in effect-verification reliability may be highly material for financial tools.

---

# 27. E22 — Rollback

Rollback occurs when:

* Security guardrail fails.
* Effect discrepancy occurs.
* Contract incompatibility appears.
* Error rate materially increases.
* Evidence coverage falls.
* Cost exceeds limits.
* Latency violates critical SLOs.
* Candidate causes caller failures.
* Tool-selection performance declines materially.

```text
Candidate guardrail failure
        ↓
Stop new candidate assignments
        ↓
Route traffic to baseline
        ↓
Complete or reconcile active effects
        ↓
Preserve evidence
        ↓
Open incident where required
        ↓
Classify candidate disposition
```

## 27.1 Candidate disposition

```typescript
export type CandidateDisposition =
  | "repair_and_retest"
  | "redesign"
  | "reject"
  | "security_quarantine"
  | "defer";
```

Rollback does not erase the candidate or its evidence.

---

# 28. E23–E24 — Promotion

A promotion decision is deterministic at the final governance boundary.

```typescript
export interface PromotionDecision {
  decision:
    | "promote"
    | "continue_canary"
    | "rollback"
    | "reject";

  reasonCodes: string[];

  metricEvidenceRefs: string[];
  reviewEvidenceRefs: string[];

  decidedBy:
    | "automated_policy"
    | "release_authority";

  decidedAt: string;
}
```

## 28.1 Promotion transaction

```text
Verify candidate hash
      ↓
Verify approvals
      ↓
Verify canary report
      ↓
Set candidate as preferred revision
      ↓
Update routing indexes
      ↓
Emit tool-list change where supported
      ↓
Begin superseded-version deprecation
```

Promotion must be atomic from the registry’s perspective.

In-progress calls continue on the revision they resolved at invocation start.

---

# 29. E25 — Deprecation

Deprecation means:

* The revision remains callable temporarily.
* New callers should not adopt it.
* Existing callers receive migration guidance.
* Tool discovery may mark it as deprecated.
* Replacement information is available.
* Retirement is planned but not yet executed.

```typescript
export interface DeprecationNotice {
  toolId: string;
  versionConstraint: string;

  replacementTools: Array<{
    toolId: string;
    versionConstraint: string;
  }>;

  reason: string;
  migrationGuideRef: string;

  deprecatedAt: string;
  migrationDeadline?: string;
  earliestRetirementAt?: string;

  severity:
    | "advisory"
    | "required"
    | "urgent";
}
```

## 29.1 Discovery policy

A deprecated tool may:

* Remain visible to existing authorized callers
* Be hidden from new callers
* Include replacement guidance in its description
* Return structured deprecation warnings
* Reject new integration registrations

It should not disappear abruptly unless it is unsafe.

---

# 30. E26 — Caller migration

Migration telemetry should identify:

* Calls still using the old version
* Graphs pinned to old contracts
* Callers receiving deprecation warnings
* Failed compatibility adapters
* Owners who have not acknowledged migration
* Requests that cannot be translated safely

```typescript
export interface MigrationStatus {
  totalKnownCallers: number;
  migratedCallers: number;
  blockedCallers: number;
  inactiveCallers: number;

  legacyInvocationRate: number;

  blockers: MigrationBlocker[];

  readyForRetirement: boolean;
}
```

## 30.1 Internal graph migration

Internal ServiceFabric graphs should use explicit tool-version constraints.

```yaml
tools:
  - id: research.search_papers
    versionConstraint: "^2.0"
```

Migration should include:

* Graph recompilation
* Contract validation
* Test execution
* Agent-callability reevaluation
* Canary deployment of dependent graphs

## 30.2 External MCP callers

ServiceFabric may not know every external client implementation.

Migration support should therefore include:

* Deprecation metadata
* Structured warnings
* Replacement tool identifiers
* Compatibility period
* Documentation
* Stable protocol errors after retirement

---

# 31. E27–E28 — Retirement

A tool or revision may be retired when:

* No active supported callers remain.
* Migration deadline has passed.
* Replacement capacity is healthy.
* Required historical data is archived.
* No unresolved effects remain.
* No active long-running operations depend on it.
* Rollback obligations have expired or are covered elsewhere.
* Owners approve retirement.
* Security and compliance retention requirements are met.

```typescript
export interface RetirementDecision {
  toolId: string;
  revisionIds: string[];

  ready: boolean;
  blockerCodes: string[];

  archiveRefs: string[];
  replacementRefs: string[];

  approvedBy: string[];
  effectiveAt?: string;
}
```

## 31.1 Retirement actions

```text
Stop new invocations
      ↓
Complete or migrate active operations
      ↓
Remove from normal discovery
      ↓
Preserve contract and documentation history
      ↓
Archive implementation artifacts
      ↓
Revoke provider credentials where dedicated
      ↓
Remove unused deployments
      ↓
Close deprecation notice
```

Retirement does not delete audit history.

---

# 32. Provider evolution

Provider changes may be evolutionary even when the public contract remains stable.

Triggers:

* API version change
* Provider deprecation
* Schema drift
* Authentication change
* Cost increase
* Quality decline
* Jurisdiction change
* New provider availability
* Rate-limit change
* External MCP tool-list change

## 32.1 Provider substitution

A provider can be replaced through a patch only when:

* Public semantics remain unchanged.
* Quality remains within guarantees.
* Freshness remains compatible.
* Evidence format remains compatible.
* Data policy permits the replacement.
* No new caller authorization is needed.

Otherwise, the change may require a minor or major revision.

## 32.2 Provider concentration

The evolution graph should monitor whether a nominally multi-provider tool has become operationally dependent on one provider.

Persistent fallback use can reveal that:

* The primary provider is no longer viable.
* Routing priorities are wrong.
* The fallback should become primary.
* The tool’s advertised resilience is misleading.

---

# 33. Model and prompt evolution

Prompts and model configurations are behaviourally relevant artifacts.

A changed prompt, model, routing strategy, or structured-output constraint must produce a new ToolRevision hash.

## 33.1 Model evolution tests

* Historical replay
* Output-schema validity
* Quality benchmarks
* Hallucination rate
* Evidence faithfulness
* Tool-call count
* Cost
* Latency
* Injection resistance
* Cross-model consistency
* Deterministic fallback behaviour

## 33.2 Model substitution

A new model may be a patch when:

* Public semantics remain stable.
* Quality and safety thresholds are maintained.
* Data policy remains unchanged.
* Cost and latency remain within guarantees.
* No new model capability is exposed to callers.

A model change that introduces new autonomous behaviour requires broader review.

---

# 34. Maintenance-graph evolution

Maintenance graphs should evolve when:

* Recovery repeatedly fails.
* Retry policy causes excessive latency.
* Fallback quality is poor.
* Provider routing is inefficient.
* Effect reconciliation is incomplete.
* Quarantine triggers are too weak.
* Partial-result classification is inaccurate.
* Model-assisted maintenance adds unnecessary variability.

Every maintenance-graph change must test:

* All routes terminate.
* Retry loops remain bounded.
* Fallback loops remain bounded.
* Policy gates remain unavoidable.
* Effect uncertainty cannot return success.
* Tool and model allowlists remain enforced.
* New recovery paths preserve contract semantics.

---

# 35. Policy evolution

Policy changes require special treatment.

## 35.1 Non-breaking policy changes

Potential examples:

* Stricter internal logging redaction
* Provider credential rotation
* Additional internal audit evidence
* Restrictive network allowlist update that preserves operation

## 35.2 Caller-visible policy changes

Potentially breaking:

* New required scope
* New approval requirement
* Reduced data access
* New tenant restriction
* New geographic limitation
* New maximum transaction value

A more secure policy may still require a major tool version or migration process when existing callers can no longer invoke the tool as before.

Security urgency may justify rapid deprecation, but not silent incompatibility.

---

# 36. MCP projection evolution

MCP projection changes should be classified separately from domain-contract changes.

```typescript
export interface McpProjectionEvolution {
  baselineProfile: string;
  targetProfile: string;

  domainContractChanged: boolean;
  protocolShapeChanged: boolean;

  compatibilityAdapterAvailable: boolean;

  conformanceReports: string[];
}
```

Examples:

* Updating SDK internals with identical MCP behaviour: patch
* Adding optional protocol metadata: patch or minor
* Adopting a new released MCP profile: protocol migration
* Changing input schema because of MCP limitations: potentially domain breaking
* Moving long-running work to a future task extension: protocol and operational compatibility analysis required

ServiceFabric should retain the canonical invocation API even when MCP protocol mechanics evolve.

---

# 37. Evolution experiments and side effects

Experiments involving state-changing tools require stricter controls.

## 37.1 Permitted methods

* Sandbox provider
* Test account
* Synthetic target
* Action-preview comparison
* Validation-only execution
* Read-after-write with immediate cleanup
* Human-supervised limited canary

## 37.2 Prohibited uncontrolled experiments

* Duplicate real payments
* Duplicate external communications
* Random user assignment to irreversible writes
* Production code changes without rollback
* Shadow execution that commits real effects
* Candidate use of approval intended for the baseline when action hashes differ

Each effectful candidate requires its own approval binding where the proposed action differs.

---

# 38. Privacy and evaluation datasets

```typescript
export interface EvolutionDataPolicy {
  permittedSources: string[];

  argumentRetention:
    | "none"
    | "hash"
    | "redacted"
    | "encrypted";

  resultRetention:
    | "none"
    | "metadata"
    | "redacted"
    | "encrypted";

  productionReplayPermitted: boolean;
  syntheticReplacementRequired: boolean;

  modelAccessClassification: string;
  retentionPeriod: string;
}
```

The evolution graph should prefer:

* Aggregated metrics
* Redacted traces
* Synthetic cases
* Recorded provider fixtures
* Minimal representative samples

Full production content should be used only where necessary and authorized.

---

# 39. Evolution decision records

```typescript
export interface EvolutionDecisionRecord {
  decisionId: string;
  evolutionRunId: string;

  stage: string;

  question: string;
  selectedOption: string;
  alternatives: string[];

  reasonCodes: string[];
  evidenceRefs: string[];

  decisionMaker:
    | "deterministic_rule"
    | "analysis_agent"
    | "policy_engine"
    | "human_reviewer";

  artifactHash?: string;
  createdAt: string;
}
```

Important recorded decisions include:

* Whether evolution is justified
* Root-cause selection
* Evolution target
* Tool split or merge
* Agentic-backing change
* Version classification
* Experiment design
* Canary expansion
* Promotion
* Deprecation
* Retirement

The record contains conclusions and evidence, not private model reasoning.

---

# 40. Evolution issues

```typescript
export interface EvolutionIssue {
  code: string;

  severity:
    | "info"
    | "warning"
    | "error"
    | "critical";

  category:
    | "evidence"
    | "diagnosis"
    | "compatibility"
    | "security"
    | "quality"
    | "migration"
    | "experiment"
    | "deployment"
    | "retirement";

  message: string;
  evidenceRefs: string[];

  repairable: boolean;
  repairStage?: string;
  humanReviewRequired: boolean;
}
```

Stable prefixes:

```text
SF-EVID-*      Evidence quality
SF-DIAG-*      Diagnosis
SF-COMPAT-*    Compatibility
SF-EXPER-*     Experiment
SF-CANARY-*    Canary
SF-MIGRATE-*   Migration
SF-DEPREC-*    Deprecation
SF-RETIRE-*    Retirement
SF-EVOL-*      General evolution
```

---

# 41. Evolution budgets

```typescript
export interface EvolutionBudget {
  maximumDuration: string;

  maximumAnalysisCalls: number;
  maximumBuildAttempts: number;
  maximumRepairCycles: number;

  maximumReplayInvocations: number;
  maximumShadowInvocations: number;
  maximumCanaryInvocations?: number;

  maximumModelTokens?: number;
  maximumCostUsd: number;
}
```

An evolution run must terminate or request explicit extension when its budget is exhausted.

The graph must not continue experiments indefinitely merely because results are inconclusive.

---

# 42. Evolution graph node interface

```typescript
export interface EvolutionGraphNode<
  TInput = ToolEvolutionState,
  TOutput = Partial<ToolEvolutionState>
> {
  id: string;
  version: string;

  type:
    | "deterministic"
    | "analysis_agent"
    | "generation_agent"
    | "evaluation"
    | "execution"
    | "human_gate"
    | "transaction";

  execute(
    state: TInput,
    context: EvolutionNodeContext
  ): Promise<EvolutionNodeResult<TOutput>>;
}
```

```typescript
export interface EvolutionNodeContext {
  runId: string;

  signal: AbortSignal;
  deadline: Date;

  registry: ToolRegistryClient;
  telemetry: EvolutionTelemetryClient;
  incidents: IncidentService;

  buildingGraph: BuildingGraphClient;
  deployment: DeploymentController;
  migrations: MigrationService;

  evaluations: EvaluationService;
  experiments: ExperimentService;

  policies: EvolutionPolicyClient;

  tools: RestrictedEvolutionToolClient;
  models: RestrictedEvolutionModelClient;

  artifacts: EvolutionArtifactStore;
  audit: AuditRecorder;
  budget: EvolutionBudgetController;
}
```

```typescript
export type EvolutionNodeResult<T> =
  | {
      outcome: "completed";
      statePatch: T;
      nextNode?: string;
    }
  | {
      outcome: "observation_required";
      observationPlan: ObservationPlan;
    }
  | {
      outcome: "repair_required";
      issues: EvolutionIssue[];
      nextNode: string;
    }
  | {
      outcome: "human_review_required";
      reviewRequest: ReviewRequest;
    }
  | {
      outcome: "rejected";
      issues: EvolutionIssue[];
    }
  | {
      outcome: "failed";
      error: ToolError;
    };
```

---

# 43. Declarative evolution graph

```yaml
apiVersion: servicefabric.ai/v1alpha1
kind: SystemEvolutionGraph

metadata:
  id: standard-tool-evolution
  version: 1.0.0
  owner: servicefabric-platform

spec:
  entryNode: validate-request

  budgets:
    maximumDuration: P14D
    maximumAnalysisCalls: 30
    maximumBuildAttempts: 3
    maximumRepairCycles: 12
    maximumCostUsd: 100

  nodes:
    validate-request:
      type: deterministic
      handler: evolution.validate-request
      next: load-baseline

    load-baseline:
      type: deterministic
      handler: evolution.load-baseline
      next: aggregate-evidence

    aggregate-evidence:
      type: deterministic
      handler: evolution.aggregate-evidence
      next: qualify

    qualify:
      type: deterministic
      handler: evolution.qualify
      routes:
        justified: reproduce
        maintenance_only: return-to-maintenance
        insufficient_evidence: observe
        duplicate: join-existing
        invalid: reject

    reproduce:
      type: execution
      handler: evolution.reproduce
      routes:
        reproduced: diagnose
        not_reproduced: observe
        unsafe_to_reproduce: diagnose-from-evidence

    diagnose:
      type: analysis_agent
      handler: evolution.diagnose-root-cause
      outputSchemaRef: schemas/root-cause-analysis.json
      next: affected-scope

    affected-scope:
      type: deterministic
      handler: evolution.determine-scope
      next: select-target

    select-target:
      type: analysis_agent
      handler: evolution.select-target
      routes:
        configuration: design-experiment
        patch: design-candidate
        minor: design-candidate
        major: design-candidate
        split: design-candidate
        merge: design-candidate
        composite: design-candidate
        new_tool: design-candidate
        deprecate: deprecation-plan
        retire: retirement-readiness

    design-candidate:
      type: generation_agent
      handler: evolution.design-candidate
      next: compatibility

    compatibility:
      type: deterministic
      handler: evolution.analyse-compatibility
      next: migration-plan

    migration-plan:
      type: generation_agent
      handler: evolution.design-migration
      next: design-experiment

    design-experiment:
      type: analysis_agent
      handler: evolution.design-experiment
      next: proposal-review

    proposal-review:
      type: human_gate
      handler: evolution.review-proposal
      routes:
        approved: build-candidate
        changes_requested: route-changes
        rejected: reject

    build-candidate:
      type: execution
      handler: evolution.invoke-building-graph
      routes:
        built: verify-candidate
        repair: design-candidate
        failed: reject

    verify-candidate:
      type: evaluation
      handler: evolution.verify-candidate
      routes:
        pass: historical-replay
        repair: design-candidate
        reject: reject

    historical-replay:
      type: evaluation
      handler: evolution.run-historical-replay
      routes:
        pass: comparative-evaluation
        regression: design-candidate

    comparative-evaluation:
      type: evaluation
      handler: evolution.compare-baseline-candidate
      routes:
        pass: shadow
        regression: design-candidate
        inconclusive: observe

    shadow:
      type: execution
      handler: evolution.run-shadow
      routes:
        pass: canary-readiness
        regression: rollback-candidate
        inconclusive: extend-shadow

    canary-readiness:
      type: deterministic
      handler: evolution.check-canary-readiness
      routes:
        ready: deploy-canary
        blocked: route-canary-blocker

    deploy-canary:
      type: transaction
      handler: evolution.deploy-canary
      next: observe-canary

    observe-canary:
      type: evaluation
      handler: evolution.observe-canary
      routes:
        pass: promotion-decision
        continue: observe-canary
        reduce: reduce-canary
        fail: rollback-candidate

    rollback-candidate:
      type: transaction
      handler: evolution.rollback-candidate
      next: candidate-disposition

    candidate-disposition:
      type: human_gate
      handler: evolution.decide-candidate-disposition
      routes:
        repair: design-candidate
        redesign: diagnose
        reject: reject
        defer: observe

    promotion-decision:
      type: human_gate
      handler: evolution.decide-promotion
      routes:
        promote: promote
        continue: observe-canary
        rollback: rollback-candidate
        reject: reject

    promote:
      type: transaction
      handler: evolution.promote-revision
      next: deprecation-plan

    deprecation-plan:
      type: deterministic
      handler: evolution.create-deprecation-plan
      next: migrate-callers

    migrate-callers:
      type: execution
      handler: evolution.migrate-callers
      routes:
        complete: retirement-readiness
        blocked: migration-review
        in_progress: migrate-callers

    retirement-readiness:
      type: deterministic
      handler: evolution.check-retirement-readiness
      routes:
        ready: retire
        not_ready: observe-retirement

    retire:
      type: transaction
      handler: evolution.retire-revision
      next: close-run

    close-run:
      type: transaction
      handler: evolution.close-run
```

---

# 44. Specialized evolution profiles

## 44.1 Description and schema profile

Use for:

* Tool-selection confusion
* Repeated invalid arguments
* Misinterpreted warnings
* Poor field descriptions

Focus:

* Selection evaluations
* Argument-construction evaluations
* Compatibility
* Minimal canary
* No implementation change where possible

## 44.2 Provider profile

Use for:

* API drift
* Cost changes
* Provider quality changes
* External MCP changes

Focus:

* Contract fixtures
* Provider comparison
* Provenance
* Rate limits
* Data policy
* Fallback behaviour

## 44.3 Agentic profile

Use for:

* Model change
* Prompt change
* Internal graph change
* Tool-use strategy change

Focus:

* Historical replay
* Variability
* Hallucination
* Tool-call amplification
* Cost
* Stopping conditions
* Injection resistance

## 44.4 Effectful-tool profile

Use for:

* Task creation
* Email
* Calendar changes
* Repository mutation
* Financial actions

Focus:

* Sandbox execution
* Idempotency
* Approval binding
* Effect verification
* Reconciliation
* Human-supervised canary

## 44.5 Protocol profile

Use for:

* MCP version changes
* SDK migration
* Transport changes
* New extensions

Focus:

* Dual compatibility
* Conformance
* Connection lifecycle
* Authorization
* Error semantics
* Client interoperability

---

# 45. Reference evolution: `research.search_papers`

```text
Signal:
    DOI validity fell from 99% to 94%.

Evidence:
    Invalid identifiers originate mainly from one provider.

Diagnosis:
    Provider changed identifier normalization.

Target:
    Patch revision.

Candidate:
    Updated provider mapper.
    New DOI normalization.
    Contract-drift detection.
    No public schema change.

Evaluation:
    Historical provider fixtures.
    Invalid-DOI cases.
    Cross-provider comparison.
    Agent-callability regression suite.

Shadow:
    Candidate validates live records without serving results.

Canary:
    5% of read-only calls.

Promotion condition:
    DOI validity ≥ 99%.
    No material latency or cost regression.

Version:
    1.3.2 → 1.3.3.
```

---

# 46. Reference evolution: calculator

```text
Signal:
    Expressions using scientific notation fail.

Diagnosis:
    Parser grammar lacks exponent notation.

Target:
    Minor compatible extension.

Candidate:
    Extend grammar.
    Preserve all existing expression semantics.

Tests:
    Existing arithmetic corpus.
    Scientific notation.
    Complexity attacks.
    Property-based comparisons.

Agent evaluation:
    Ensure agents do not use the calculator for data retrieval.

Canary:
    Low-risk automated canary.

Version:
    1.0.4 → 1.1.0.
```

---

# 47. Reference evolution: task creation

```text
Signal:
    Duplicate tasks appear after provider timeouts.

Diagnosis:
    Provider accepts an idempotency field, but the adapter
    does not transmit the ServiceFabric key.

Risk:
    Reversible external write.

Target:
    Patch revision.

Candidate:
    Map ServiceFabric idempotency key.
    Add effect reconciliation.
    Add duplicate-detection tests.

Experiment:
    Sandbox provider and fault injection.

Canary:
    Internal test projects only.
    Human-supervised first production calls.

Promotion condition:
    Zero duplicates under timeout simulation.
    Effect verification rate 100%.
```

---

# 48. Reference evolution: recurring composition

```text
Signal:
    External research graphs invoke:
      1. research.search_papers
      2. research.retrieve_metadata
      3. research.validate_citations

    in the same order on 72% of research runs.

Diagnosis:
    Sequence has one bounded outcome:
    a validated evidence set.

Target:
    Create composite tool:
    research.build_evidence_set

Decision:
    Preserve primitive tools.
    Introduce composite as an additional capability.

Agentic backing:
    Assisted for ranking and contradiction grouping.
    Deterministic citation validation.

Version impact:
    New tool, no breaking change to existing tools.
```

---

# 49. Evolution performance metrics

```text
evolution_signals_total
evolution_requests_qualified_total
evolution_requests_rejected_total
evolution_reproduction_rate
evolution_root_cause_confidence
evolution_build_attempts
evolution_candidate_regressions
evolution_shadow_failures
evolution_canary_rollbacks
evolution_promotions
evolution_time_to_candidate
evolution_time_to_promotion
evolution_migration_completion_rate
evolution_legacy_invocation_rate
evolution_retirements
```

Quality metrics:

```text
issue_recurrence_rate
post_evolution_error_delta
post_evolution_quality_delta
post_evolution_latency_delta
post_evolution_cost_delta
agent_selection_improvement
argument_validity_improvement
maintenance_intervention_reduction
fallback_rate_reduction
incident_rate_delta
```

A successful evolution should reduce the triggering problem measurably.

---

# 50. Evolution service objectives

Illustrative objectives:

```yaml
criticalSecuritySignalQualification: PT15M
highSeveritySignalQualification: PT4H
ordinarySignalQualification: P3D

reproducibleIssueTargetRate: 0.90
candidateOutputValidityRate: 1.0
effectVerificationRate: 1.0

criticalCanaryRollbackDetection: PT1M
migrationVisibilityRate: 1.0
retirementDependencyVerificationRate: 1.0
```

These objectives should vary by tool risk.

---

# 51. System-evolution invariants

```text
SF-E001  Published ToolRevisions are immutable.
SF-E002  Every evolution request identifies a baseline.
SF-E003  Every evolution is supported by evidence.
SF-E004  Temporary incidents are not automatically treated as design defects.
SF-E005  Evolution attempts to reproduce the qualifying problem.
SF-E006  Every candidate has a structured root-cause analysis.
SF-E007  Every candidate has an explicit change classification.
SF-E008  Every caller-visible change receives compatibility analysis.
SF-E009  Every breaking change requires a migration plan.
SF-E010  Every candidate receives a semantic-version classification.
SF-E011  Evolution does not bypass the system-building graph.
SF-E012  Every candidate passes normal publication gates.
SF-E013  Every candidate is compared with its baseline.
SF-E014  Historical failure cases become regression tests.
SF-E015  Shadow executions cannot commit external effects.
SF-E016  Effectful canaries use restricted targets and approval.
SF-E017  Every canary has deterministic stopping rules.
SF-E018  Security guardrail failure causes immediate rollback.
SF-E019  Every promotion is bound to a candidate artifact hash.
SF-E020  In-progress calls remain on their resolved revision.
SF-E021  Rollback preserves candidate evidence.
SF-E022  Deprecation precedes ordinary retirement.
SF-E023  Retirement requires dependency verification.
SF-E024  Retirement does not delete audit history.
SF-E025  Compatibility adapters cannot weaken security.
SF-E026  Compatibility adapters have explicit expiry.
SF-E027  Model and prompt changes create new revision hashes.
SF-E028  Agentic-backing increases require explicit justification.
SF-E029  Evolution agents cannot grant authorization.
SF-E030  Evolution agents cannot suppress incidents.
SF-E031  Provider changes remain subject to data policy.
SF-E032  Protocol evolution remains separate from domain semantics.
SF-E033  Preview protocol profiles cannot silently become production.
SF-E034  Recurring composition is evaluated before creating composites.
SF-E035  Tool splits preserve migration paths where feasible.
SF-E036  Tool merges do not conceal differing side effects.
SF-E037  Every evolution loop is bounded.
SF-E038  Inconclusive experiments do not imply promotion.
SF-E039  A candidate must resolve the qualifying issue measurably.
SF-E040  Maintenance graphs emit evidence; evolution graphs redesign.
```

---

# 52. Architectural decision

ServiceFabric should treat evolution as a governed **champion–challenger lifecycle**.

```text
Champion
    Active stable revision
        │
        ├── operational evidence
        │
        └── evolution signal
                 ↓
Challenger
    Newly built candidate revision
        │
        ├── offline comparison
        ├── historical replay
        ├── shadow execution
        └── canary
                 ↓
        Promotion decision
          ├── promote challenger
          ├── continue experiment
          ├── repair challenger
          └── retain champion
```

The three-graph lifecycle is therefore complete:

```text
SYSTEM-BUILDING GRAPH
    Creates governed capabilities
             ↓
       ToolRevision
             ↓
SYSTEM-MAINTENANCE GRAPH
    Supports calls and produces evidence
             ↓
       EvolutionSignal
             ↓
SYSTEM-EVOLUTION GRAPH
    Designs and validates replacement behaviour
             ↓
SYSTEM-BUILDING GRAPH
    Constructs the next immutable revision
```

This closed loop allows ServiceFabric to improve continuously without allowing live tools to rewrite themselves or drift beyond their declared contracts.
