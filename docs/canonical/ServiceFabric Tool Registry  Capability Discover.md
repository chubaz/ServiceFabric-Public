# ServiceFabric Tool Registry, Capability Discovery, and Routing Specification v1

**Status:** Architecture baseline
**Subsystem:** Tool control plane
**API version:** `servicefabric.ai/v1alpha1`
**Primary responsibilities:** Registration, discovery, resolution, compatibility, authorization-aware listing, and runtime routing

---

# 1. Purpose

The **ServiceFabric Tool Registry** is the authoritative catalogue of tool capabilities and their deployable revisions.

It enables internal and external graphs to:

* Discover relevant capabilities
* Compare similar tools
* Understand contracts and limitations
* Determine whether a tool is callable
* Resolve a stable revision
* Select an appropriate deployment
* Avoid loading the full tool catalogue into model context
* Route calls without exposing provider-level complexity
* Track dependencies, versions, deprecations, and replacements

```text
ToolDefinition
      ↓
ToolRevision
      ↓
ToolDeployment
      ↓
ToolStatus
      ↓
Registry indexes
      ↓
Capability discovery
      ↓
Revision and deployment resolution
      ↓
Tool invocation
```

The registry is both:

```text
A catalogue
    What capabilities exist?

A control plane
    Which revision and deployment should handle this call?
```

---

# 2. Architectural boundary

The registry stores and resolves capability metadata. It does not execute tools.

```text
Registry
    Identifies and resolves tools

Invocation runtime
    Executes resolved tools

Maintenance system
    Maintains tool and provider health

Policy service
    Decides whether callers may use tools

Building graph
    Publishes immutable revisions

Evolution graph
    Publishes replacements and lifecycle changes
```

The registry may consume policy and health information, but it must not become the authoritative source for either.

---

# 3. Primary design problem

A large agentic platform may contain hundreds or thousands of tools.

Sending every tool definition to a model creates:

* Context-window waste
* Selection errors
* Similar-tool confusion
* Increased latency and cost
* Provider-specific leakage
* Security exposure
* Prompt-injection surface
* Poor tool-call precision

ServiceFabric should therefore use progressive capability discovery.

```text
User or graph intent
        ↓
Capability-domain retrieval
        ↓
Small candidate set
        ↓
Detailed contract retrieval
        ↓
Authorization filtering
        ↓
Compatibility and health filtering
        ↓
Ranked callable tool set
```

A model should normally receive between approximately 3 and 15 candidate tools, not the entire platform catalogue.

---

# 4. Registry resource model

```text
CapabilityDefinition
    Abstract domain capability

ToolDefinition
    Canonical caller-facing contract

ToolRevision
    Immutable built realization

ToolDeployment
    Runtime placement

ToolStatus
    Observed operational state

ToolRelationship
    Similarity, replacement, dependency, composition

CapabilityIndex
    Search and retrieval structures

ToolAccessProjection
    Caller-specific discoverable view
```

---

# 5. CapabilityDefinition

A `CapabilityDefinition` represents an abstract operation independent of one specific implementation.

```yaml
apiVersion: servicefabric.ai/v1alpha1
kind: CapabilityDefinition

metadata:
  id: research.scholarship_search
  title: Scholarly Literature Search
  domain: research

spec:
  objective: >
    Discover scholarly records relevant to a research question.

  capabilityClass: retrieval

  concepts:
    - academic literature
    - scholarly papers
    - scientific publications
    - citations
    - DOI
    - arXiv

  expectedInputs:
    - research query
    - date constraints
    - result limit

  expectedOutputs:
    - ranked scholarly records
    - identifiers
    - provenance

  effectClass: read_external

  suitableFor:
    - literature review
    - evidence discovery
    - research planning

  unsuitableFor:
    - full-text retrieval
    - quotation verification
    - general web search

  qualityDimensions:
    - relevance
    - identifier validity
    - coverage
    - freshness
    - provenance
```

Several tools or revisions may implement one abstract capability.

```text
research.scholarship_search
        ├── research.search_papers
        ├── research.search_preprints
        └── federated provider tools
```

The registry should normally expose the stable ServiceFabric tool rather than provider-specific variants.

---

# 6. Registry records

## 6.1 Tool catalogue record

```typescript
export interface ToolCatalogueRecord {
  toolId: string;
  currentVersion: string;

  title: string;
  description: string;

  domain: string;
  capabilityClass: string;
  capabilityIds: string[];

  owners: {
    technical: string[];
    business: string[];
  };

  lifecycle:
    | "draft"
    | "active"
    | "degraded"
    | "deprecated"
    | "retired"
    | "quarantined";

  effects: {
    class: string;
    readOnly: boolean;
    destructive: boolean;
    reversible: boolean;
    idempotent: boolean;
    openWorld: boolean;
  };

  agenticBacking: {
    level: string;
    modelUse: boolean;
  };

  discovery: ToolDiscoveryMetadata;

  activeRevisionIds: string[];
  replacementToolIds: string[];
}
```

## 6.2 Revision record

```typescript
export interface ToolRevisionRecord {
  revisionId: string;
  toolId: string;
  version: string;

  definitionHash: string;
  artifactHash: string;

  createdAt: string;
  publishedAt: string;

  lifecycle:
    | "published"
    | "active"
    | "deprecated"
    | "retired"
    | "quarantined";

  interface: {
    inputSchemaRef: string;
    outputSchemaRef: string;
    errorCatalogueRef: string;
  };

  implementation: {
    adapter: string;
    artifactRef: string;
  };

  maintenanceGraphRef: string;
  policyBundleRef: string;
  evaluationReportRef: string;
  mcpProjectionRef?: string;

  compatibility: {
    predecessors: string[];
    semanticVersion: string;
  };
}
```

## 6.3 Deployment record

```typescript
export interface ToolDeploymentRecord {
  deploymentId: string;
  revisionId: string;

  environment:
    | "development"
    | "testing"
    | "staging"
    | "production";

  region: string;
  tenantScope?: string;

  endpointRef: string;
  runtime: string;

  trafficWeight: number;

  state:
    | "provisioning"
    | "ready"
    | "degraded"
    | "draining"
    | "unavailable";

  supportedProtocols:
    | Array<"internal" | "mcp" | "rest">;

  deployedAt: string;
}
```

---

# 7. Discovery metadata

Tool descriptions for retrieval require richer semantics than the concise MCP description.

```typescript
export interface ToolDiscoveryMetadata {
  summary: string;

  whenToUse: string[];
  whenNotToUse: string[];

  intents: string[];
  concepts: string[];
  entities: string[];

  inputConcepts: string[];
  outputConcepts: string[];

  exampleRequests: string[];
  negativeExamples: string[];

  domains: string[];
  industries?: string[];

  callerTypes: string[];

  equivalentCapabilities: string[];
  adjacentCapabilities: string[];

  searchAliases: string[];
}
```

The concise MCP descriptor is generated from this richer representation.

---

# 8. Capability ontology

ServiceFabric should maintain a lightweight capability ontology.

```text
Domain
  └── Capability family
        └── Capability
              └── Tool
                    └── Revision
                          └── Deployment
```

Example:

```text
Research
  ├── Discovery
  │     ├── Web search
  │     ├── Scholarly search
  │     └── Dataset search
  │
  ├── Retrieval
  │     ├── Retrieve webpage
  │     ├── Retrieve paper
  │     └── Retrieve dataset
  │
  ├── Verification
  │     ├── Verify citation
  │     ├── Verify quotation
  │     └── Validate identifier
  │
  └── Synthesis
        ├── Build evidence set
        └── Compare findings
```

The ontology should remain practical rather than philosophically exhaustive.

Its purpose is to improve:

* Discovery
* Tool differentiation
* Composition
* Coverage analysis
* Gap detection
* Evolution decisions

---

# 9. Initial capability classes

```text
computation
retrieval
transformation
analysis
generation
verification
action
coordination
administration
observation
communication
meta
```

## 9.1 Meta-capabilities

Meta-tools operate on ServiceFabric itself.

Examples:

```text
registry.search_capabilities
registry.describe_tool
registry.compare_tools
registry.list_replacements
registry.resolve_version
registry.explain_unavailability
registry.report_tool_gap
registry.request_evolution
```

These are important for advanced agent frameworks because they allow an agent to reason about its available actions without receiving the entire catalogue at once.

---

# 10. Search indexes

The registry should maintain multiple indexes rather than rely on one search mechanism.

```text
Exact identifier index
Keyword index
Semantic vector index
Capability ontology index
Input/output concept index
Effect index
Owner and domain index
Relationship graph
Lifecycle index
Authorization projection index
Health and deployment index
```

## 10.1 Exact index

Used for:

* Tool ID
* Version
* Revision ID
* Capability ID
* Owner
* Tag
* Domain

## 10.2 Keyword index

Used for:

* Descriptions
* Aliases
* Example requests
* Concepts
* Error codes
* Input and output field descriptions

## 10.3 Semantic index

Used for matching natural-language intent to:

* Capability summaries
* Appropriate-use examples
* Inappropriate-use examples
* Expected inputs and outputs
* Domain concepts

## 10.4 Relationship graph

Used for:

* Replacements
* Dependencies
* Alternatives
* Composition
* Similarity
* Provider realization
* Version succession
* Deprecation migration

---

# 11. Tool relationships

```typescript
export type ToolRelationshipType =
  | "implements_capability"
  | "depends_on"
  | "alternative_to"
  | "replaces"
  | "supersedes"
  | "deprecated_by"
  | "composes"
  | "often_precedes"
  | "often_follows"
  | "confused_with"
  | "provider_variant_of"
  | "requires_output_of"
  | "incompatible_with";
```

```typescript
export interface ToolRelationship {
  sourceToolId: string;
  targetToolId: string;

  type: ToolRelationshipType;

  confidence?: number;
  evidenceRefs?: string[];

  validFrom: string;
  validUntil?: string;
}
```

Examples:

```text
research.retrieve_paper
    often_follows
research.search_papers

finance.calculate_portfolio_risk
    requires_output_of
finance.retrieve_market_data

project.create_task
    alternative_to
project.create_issue

research.build_evidence_set
    composes
research.search_papers
research.retrieve_metadata
research.validate_citations
```

---

# 12. Discovery API

## 12.1 Capability search

```typescript
export interface CapabilitySearchRequest {
  query: string;

  caller: CallerContext;

  domains?: string[];
  capabilityClasses?: string[];
  effectClasses?: string[];

  requiredInputs?: string[];
  requiredOutputs?: string[];

  maximumResults?: number;

  includeDeprecated?: boolean;
  includeUnavailable?: boolean;

  context?: {
    parentGraphId?: string;
    precedingToolIds?: string[];
    availableDataTypes?: string[];
    desiredEffectClass?: string;
  };
}
```

```typescript
export interface CapabilitySearchResult {
  queryInterpretation: {
    objective: string;
    concepts: string[];
    requiredInputs: string[];
    requiredOutputs: string[];
    prohibitedEffects: string[];
  };

  candidates: ToolCandidateSummary[];

  gaps: CapabilityGap[];

  searchMeta: {
    totalCandidatesEvaluated: number;
    authorizationFiltered: number;
    healthFiltered: number;
    compatibilityFiltered: number;
  };
}
```

## 12.2 Candidate summary

```typescript
export interface ToolCandidateSummary {
  toolId: string;
  versionConstraint: string;

  title: string;
  conciseDescription: string;

  capabilityMatchScore: number;
  suitabilityScore: number;

  effectClass: string;
  approvalRequired: boolean;

  availability:
    | "available"
    | "degraded"
    | "approval_required"
    | "unavailable";

  reasonCodes: string[];

  limitations: string[];
}
```

The summary should be compact enough for model context.

---

# 13. Progressive discovery

ServiceFabric should use three discovery depths.

## 13.1 Level 1 — Capability cards

Used to shortlist candidates.

```json
{
  "toolId": "research.search_papers",
  "title": "Scholarly Paper Search",
  "summary": "Find scholarly records with identifiers and provenance.",
  "effectClass": "read_external",
  "availability": "available",
  "suitabilityScore": 0.94
}
```

## 13.2 Level 2 — Selection cards

Used by a model choosing among a small set.

```json
{
  "toolId": "research.search_papers",
  "description": "Search scholarly sources for academic papers.",
  "whenToUse": [
    "Academic literature discovery",
    "DOI or arXiv identification"
  ],
  "whenNotToUse": [
    "General web search",
    "Full-text retrieval",
    "Quotation verification"
  ],
  "requiredInputs": [
    "query"
  ],
  "effectClass": "read_external",
  "approvalRequired": false
}
```

## 13.3 Level 3 — Invocation contract

Retrieved only after tool selection.

Contains:

* Full input schema
* Output schema
* Error catalogue
* Examples
* Version
* Approval requirements
* Effect information
* Current limitations

This prevents detailed schemas for irrelevant tools from consuming context.

---

# 14. Discovery pipeline

```text
D01 Interpret capability intent
  ↓
D02 Retrieve ontology candidates
  ↓
D03 Retrieve lexical candidates
  ↓
D04 Retrieve semantic candidates
  ↓
D05 Merge and deduplicate
  ↓
D06 Filter lifecycle state
  ↓
D07 Filter authorization visibility
  ↓
D08 Filter effect compatibility
  ↓
D09 Filter input/output compatibility
  ↓
D10 Filter health and deployment
  ↓
D11 Rank candidates
  ↓
D12 Diversify candidate set
  ↓
D13 Generate compact tool cards
```

---

# 15. Query interpretation

The registry may use bounded model assistance to convert user or graph intent into structured search concepts.

```typescript
export interface CapabilityQueryInterpretation {
  objective: string;

  domains: string[];
  concepts: string[];

  requiredInputs: string[];
  desiredOutputs: string[];

  preferredCapabilityClasses: string[];
  prohibitedEffectClasses: string[];

  freshnessRequired?: boolean;
  externalDataRequired?: boolean;
  codeExecutionRequired?: boolean;

  uncertainty: string[];
}
```

Model assistance must not determine authorization or override effect restrictions.

A deterministic fallback should use:

* Keywords
* Domain tags
* Exact aliases
* Graph context
* Tool relationships

---

# 16. Authorization-aware discovery

The registry should not expose identical catalogues to every caller.

```text
Global tool catalogue
        ↓
Tenant visibility
        ↓
Caller role and scope
        ↓
Environment policy
        ↓
Data classification
        ↓
Effect and approval visibility
        ↓
Caller-specific tool projection
```

## 16.1 Visibility states

```typescript
export type ToolVisibility =
  | "discoverable_and_callable"
  | "discoverable_approval_required"
  | "discoverable_not_currently_callable"
  | "hidden";
```

### Discoverable and callable

The caller can invoke the tool subject to ordinary argument-level policy.

### Discoverable, approval required

The capability may be shown because the caller can request approval.

### Discoverable, unavailable

Useful when:

* Capability exists but is temporarily offline.
* A replacement can be suggested.
* The caller may choose another plan.

### Hidden

Use when:

* Caller cannot ever invoke the tool.
* Tool existence is sensitive.
* Tenant policy forbids exposure.
* Tool is quarantined for security reasons.
* Tool is internal infrastructure.

---

# 17. Authorization projection

```typescript
export interface ToolAccessProjection {
  toolId: string;
  principalId: string;
  tenantId?: string;

  visibility: ToolVisibility;

  requiredScopes: string[];
  missingScopes: string[];

  approval:
    | "not_required"
    | "required"
    | "not_available";

  effectRestrictions: string[];

  validUntil: string;
  policyDecisionId: string;
}
```

Access projections should be cached briefly and invalidated when:

* Caller scopes change.
* Tool policy changes.
* Tool revision changes.
* Tenant policy changes.
* Tool lifecycle state changes.
* A security incident occurs.

---

# 18. Candidate filtering

Before ranking, the registry removes candidates that cannot satisfy the request.

## 18.1 Lifecycle filter

Exclude:

* Retired revisions
* Draft revisions
* Quarantined tools
* Incompatible deprecated revisions

## 18.2 Capability filter

Exclude tools lacking:

* Required output
* Required operation
* Necessary freshness
* Necessary data source
* Necessary execution semantics

## 18.3 Effect filter

Example:

```text
Request requires read-only analysis
        ↓
Exclude tools that:
    send messages
    mutate files
    create transactions
    change project state
```

## 18.4 Input-availability filter

A tool may require inputs the calling graph does not possess.

Example:

```text
Tool requires accountId and portfolio holdings.
Graph currently has only a company ticker.

Result:
    lower suitability or exclude.
```

## 18.5 Health filter

Exclude or penalize:

* Unavailable deployments
* Open circuit breakers
* Invalid maintenance graph
* Failed policy enforcement
* Insufficient provider coverage

---

# 19. Ranking model

The registry should rank tool candidates through a transparent scoring model.

```typescript
export interface ToolRankingFeatures {
  semanticMatch: number;
  objectiveMatch: number;

  inputCompatibility: number;
  outputCompatibility: number;

  effectCompatibility: number;
  authorizationSuitability: number;

  healthScore: number;
  qualityScore: number;
  reliabilityScore: number;

  latencyScore: number;
  costScore: number;

  graphContextScore: number;
  historicalSuccessScore: number;

  deprecationPenalty: number;
  complexityPenalty: number;
}
```

Illustrative score:

```text
score =
    0.24 × semanticMatch
  + 0.16 × objectiveMatch
  + 0.10 × inputCompatibility
  + 0.10 × outputCompatibility
  + 0.10 × effectCompatibility
  + 0.08 × qualityScore
  + 0.06 × healthScore
  + 0.05 × reliabilityScore
  + 0.04 × graphContextScore
  + 0.03 × latencyScore
  + 0.02 × costScore
  + 0.02 × historicalSuccessScore
  - deprecationPenalty
  - complexityPenalty
```

Weights should be configurable by capability class and risk level.

A financial execution router should emphasize:

* Authorization
* Effect compatibility
* Reliability
* Idempotency
* Provider trust

A web-search router may emphasize:

* Semantic fit
* Freshness
* Coverage
* Latency

---

# 20. Ranking reason codes

Every recommendation should explain itself through concise reason codes.

```text
HIGH_SEMANTIC_MATCH
MATCHES_REQUIRED_OUTPUT
CALLER_HAS_REQUIRED_SCOPE
READ_ONLY_AS_REQUESTED
HEALTHY_DEPLOYMENT
HIGH_HISTORICAL_SUCCESS
PROVENANCE_SUPPORTED
LOWER_LATENCY
LOWER_COST
REQUIRES_MISSING_INPUT
APPROVAL_REQUIRED
DEPRECATED_VERSION
DEGRADED_PROVIDER_COVERAGE
```

Example:

```json
{
  "toolId": "research.search_papers",
  "suitabilityScore": 0.94,
  "reasonCodes": [
    "HIGH_SEMANTIC_MATCH",
    "MATCHES_REQUIRED_OUTPUT",
    "PROVENANCE_SUPPORTED",
    "CALLER_HAS_REQUIRED_SCOPE"
  ]
}
```

---

# 21. Candidate diversification

Returning five nearly identical provider variants is not useful.

The registry should diversify candidates by:

* Capability approach
* Effect class
* Data source
* Cost and latency profile
* Level of abstraction
* Primitive versus composite capability

Example:

```text
Request:
    Investigate current research on a topic.

Useful candidate set:
    research.search_papers
    web.search_pages
    research.search_datasets
    research.build_evidence_set

Poor candidate set:
    arxiv.search
    crossref.search
    semantic_scholar.search
    pubmed.search
```

Provider selection should normally remain internal to the tool.

---

# 22. Tool comparison

```typescript
export interface ToolComparisonRequest {
  toolIds: string[];
  caller: CallerContext;

  intendedObjective?: string;
  availableInputs?: string[];
  desiredOutputs?: string[];
}
```

```typescript
export interface ToolComparisonResult {
  dimensions: string[];

  tools: Array<{
    toolId: string;
    scores: Record<string, number>;
    strengths: string[];
    limitations: string[];
    requirements: string[];
    recommendation?: string;
  }>;

  preferredToolId?: string;
  rationaleCodes: string[];
}
```

Comparison dimensions:

* Objective fit
* Inputs required
* Outputs produced
* Effects
* Authorization
* Approval
* Reliability
* Freshness
* Latency
* Cost
* Evidence
* Agentic backing
* Operational availability

---

# 23. Capability gaps

The registry should identify when no current tool adequately satisfies a request.

```typescript
export interface CapabilityGap {
  objective: string;

  missingInputs?: string[];
  missingOutputs?: string[];

  nearestToolIds: string[];
  unmetRequirements: string[];

  suggestedAction:
    | "compose_existing_tools"
    | "request_tool_extension"
    | "build_new_tool"
    | "use_human_process"
    | "cannot_support";
}
```

A gap report may create:

* A system-building request
* A system-evolution request
* A graph-composition recommendation
* A human-task request

The registry should not invent or expose a weak tool solely to avoid returning a gap.

---

# 24. Runtime resolution

Discovery chooses a tool. Resolution selects a revision and deployment.

```text
Selected tool ID
      ↓
Version constraint
      ↓
Compatible active revisions
      ↓
Caller and tenant compatibility
      ↓
Protocol compatibility
      ↓
Deployment availability
      ↓
Routing policy
      ↓
ResolvedToolRevision
```

## 24.1 Resolution request

```typescript
export interface ToolResolutionRequest {
  toolId: string;
  versionConstraint?: string;

  caller: CallerContext;

  protocol:
    | "internal"
    | "mcp"
    | "rest";

  environment: string;
  region?: string;

  requirements?: {
    maximumLatencyMs?: number;
    maximumCostUsd?: number;
    requiredFreshness?: string;
    requiredOutputSchemaHash?: string;
  };

  parentGraph?: {
    graphId: string;
    graphVersion: string;
    runId: string;
  };
}
```

## 24.2 Resolution result

```typescript
export interface ToolResolutionResult {
  toolId: string;
  version: string;
  revisionId: string;

  deploymentId: string;
  endpointRef: string;

  interface: {
    inputSchemaRef: string;
    outputSchemaRef: string;
  };

  policyBundleRef: string;
  maintenanceGraphRef: string;

  lifecycleState: "active" | "degraded";

  warnings: string[];

  resolutionId: string;
  resolvedAt: string;
}
```

---

# 25. Revision selection

The registry should select the highest compatible active revision unless policy specifies otherwise.

```text
Requested constraint: ^2.1
Available:
    1.9.7
    2.1.0
    2.1.4
    2.2.0
    3.0.0

Selected:
    2.2.0
```

Selection must also consider:

* Quarantine state
* Environment approval
* Caller migration status
* Canary assignment
* Tenant compatibility
* Protocol support
* Output-schema compatibility

## 25.1 Pinned resolution

Certain workflows require exact revision pinning:

* Financial processes
* Audited reporting
* Reproducible research
* Long-running operations
* Regulated workflows
* Evaluation runs
* Incident replay

```yaml
tool:
  id: finance.calculate_nav
  revisionId: rev_01J...
```

---

# 26. Deployment routing

After revision selection, the registry or deployment router chooses a deployment.

```typescript
export interface DeploymentCandidate {
  deploymentId: string;
  revisionId: string;

  region: string;
  tenantScope?: string;

  state: string;
  trafficWeight: number;

  currentLoad: number;
  p95LatencyMs: number;
  errorRate: number;

  estimatedNetworkLatencyMs: number;

  protocolSupport: string[];

  dataResidencyCompatible: boolean;
}
```

## 26.1 Deployment-routing order

```text
Revision compatibility
      ↓
Data-residency policy
      ↓
Tenant compatibility
      ↓
Protocol compatibility
      ↓
Deployment readiness
      ↓
Canary assignment
      ↓
Load and latency
      ↓
Selected deployment
```

Health information affects routing but is owned by maintenance.

---

# 27. Canary and experiment routing

The registry applies deterministic experiment assignments.

```typescript
export interface ExperimentAssignment {
  experimentId: string;
  principalSegment?: string;
  graphSegment?: string;

  baselineRevisionId: string;
  candidateRevisionId: string;

  assignedRevisionId: string;

  assignmentReason: string;
  expiresAt: string;
}
```

Assignment should use stable hashing based on approved dimensions such as:

* Tenant
* Caller
* Graph
* Request class

The model should not decide whether a call enters an experiment.

---

# 28. Composite-tool routing

A composite tool should appear as one public capability.

```text
External caller
      ↓
research.build_evidence_set
      ↓
Resolved composite revision
      ↓
Internal graph:
    search papers
    retrieve metadata
    validate citations
```

The registry must distinguish:

* Publicly discoverable composite
* Internal component tools
* Primitive tools still available independently
* Required version combinations

```typescript
export interface CompositeToolDefinition {
  toolId: string;

  componentConstraints: Array<{
    toolId: string;
    versionConstraint: string;
  }>;

  graphRef: string;

  atomicity:
    | "all_or_nothing"
    | "partial_permitted";

  publicEffectClass: string;
}
```

---

# 29. Federated MCP registry

ServiceFabric may import tools from external MCP servers, but external definitions enter a quarantine-like staging process before public exposure.

```text
External MCP server
      ↓
Server registration
      ↓
Tool inventory import
      ↓
Schema validation
      ↓
Effect reclassification
      ↓
Security review
      ↓
ServiceFabric wrapper creation
      ↓
Registry publication
```

## 29.1 External server record

```typescript
export interface FederatedMcpServerRecord {
  serverId: string;
  title: string;

  endpointRef: string;
  transport: "streamable_http" | "stdio";

  trustLevel:
    | "untrusted"
    | "reviewed"
    | "trusted";

  authenticationRef?: string;

  supportedProtocolVersions: string[];

  toolInventoryHash?: string;
  lastInventoryRefreshAt?: string;

  state:
    | "pending_review"
    | "active"
    | "degraded"
    | "quarantined"
    | "retired";
}
```

## 29.2 Imported tool record

```typescript
export interface FederatedToolRecord {
  externalServerId: string;
  externalToolName: string;

  externalSchemaHash: string;

  serviceFabricToolId?: string;
  wrapperRevisionId?: string;

  effectAssessment: string;
  trustAssessment: string;

  exposure:
    | "internal_only"
    | "wrapped_public"
    | "rejected";
}
```

External MCP tools should not be placed directly into the ordinary model tool list without:

* ServiceFabric naming
* Description normalization
* Policy binding
* Output validation
* Error normalization
* Health supervision
* Contract-drift monitoring

---

# 30. Dynamic inventory changes

When tools are added, removed, deprecated, quarantined, or replaced, the registry emits a `ToolCatalogueChanged` event.

```typescript
export interface ToolCatalogueChanged {
  eventId: string;

  changeType:
    | "tool_added"
    | "tool_updated"
    | "tool_deprecated"
    | "tool_retired"
    | "tool_quarantined"
    | "tool_restored"
    | "access_changed";

  toolId: string;
  revisionId?: string;

  affectedTenants?: string[];
  occurredAt: string;
}
```

Consumers may:

* Invalidate tool-list caches
* Refresh MCP projections
* Recompile dependent graphs
* Update capability embeddings
* Notify owners
* Reevaluate tool selection

---

# 31. MCP tool-list projection

For MCP clients, the registry supplies a caller-specific projection.

```text
MCP tools/list
      ↓
Authenticate session
      ↓
Construct caller projection
      ↓
Filter visible tools
      ↓
Select active compatible revisions
      ↓
Generate MCP descriptors
      ↓
Paginate and return
```

The gateway should avoid exposing:

* Internal endpoints
* Provider routing
* Secret names
* Hidden tools
* Unauthorized tools
* Internal maintenance capabilities
* Deployment topology
* Private policies

---

# 32. Context-efficient tool loading

ServiceFabric should support several model-facing strategies.

## 32.1 Static small catalogue

Use when the graph has fewer than approximately 10–20 stable tools.

## 32.2 Domain catalogue

Load tools only from a relevant domain.

Example:

```text
Financial-analysis graph
    receives finance, research and calculator tools
    but not deployment or HR administration tools
```

## 32.3 Search-before-use

Give the model meta-tools:

```text
registry.search_capabilities
registry.describe_tool
```

The model first searches for capabilities, then retrieves contracts.

## 32.4 Planner-selected catalogue

A deterministic or bounded planning stage identifies required capability classes and loads only those tools.

## 32.5 Graph-compiled catalogue

A graph declares tool dependencies at build time.

```yaml
requiredCapabilities:
  - research.scholarship_search
  - research.document_retrieval
  - research.citation_validation
```

The compiler resolves compatible tools and embeds only their invocation contracts.

---

# 33. Graph tool dependencies

Graphs should depend on capabilities or stable tool IDs, not deployments.

```yaml
apiVersion: servicefabric.ai/v1alpha1
kind: AgentGraph

metadata:
  id: financial-research-agent
  version: 1.0.0

spec:
  tools:
    - capabilityId: research.scholarship_search
      versionConstraint: "^1.0"

    - toolId: finance.retrieve_filing
      versionConstraint: "^2.0"

    - toolId: math.calculate
      versionConstraint: "^1.0"
```

## 33.1 Capability dependency

Allows substitution among compatible tools.

## 33.2 Tool dependency

Requires a specific public contract.

## 33.3 Revision dependency

Requires exact reproducibility.

The graph compiler should record the final resolved dependency lock.

---

# 34. Tool-selection context

The registry may use graph context when ranking.

```typescript
export interface ToolSelectionContext {
  graphId?: string;
  graphNodeId?: string;

  userObjective?: string;
  currentSubtask?: string;

  availableArtifacts?: Array<{
    type: string;
    schemaRef?: string;
  }>;

  precedingTools?: string[];
  expectedNextOutputs?: string[];

  remainingBudget?: {
    durationMs?: number;
    costUsd?: number;
    toolCalls?: number;
  };

  maximumEffectClass?: string;
}
```

Examples:

* After `research.search_papers`, rank `research.retrieve_paper` more highly.
* When a financial report artifact already exists, rank analysis tools over retrieval tools.
* When no approval is available, exclude write tools.
* When budget is low, prefer a deterministic calculator over an agent-backed analysis tool.

---

# 35. Tool-selection memory

The registry may learn from aggregated historical performance, but historical use must not create an uncontrolled popularity bias.

Potential signals:

* Successful use for similar objectives
* Invalid-argument rate
* User correction rate
* Completion rate
* Follow-up tool patterns
* Agent-selection precision
* Failure and fallback rate

Controls:

* Minimum sample size
* Recency weighting
* Tenant separation
* Risk normalization
* Quality threshold
* Exploration allowance
* No ranking solely by invocation volume

A frequently called poor tool should not dominate discovery.

---

# 36. Tool confusion detection

The registry should maintain a confusion matrix.

```typescript
export interface ToolConfusionRecord {
  intendedToolId: string;
  selectedToolId: string;

  contextClass: string;

  occurrenceCount: number;
  correctionCount: number;

  firstObservedAt: string;
  lastObservedAt: string;
}
```

Repeated confusion may trigger:

* Description changes
* Better negative examples
* Tool merge
* Tool split
* Ranking adjustment
* Evolution signal

---

# 37. Tool registry APIs

Recommended internal APIs:

```text
registry.register_definition
registry.publish_revision
registry.register_deployment
registry.update_lifecycle
registry.get_tool
registry.get_revision
registry.get_contract
registry.search_capabilities
registry.compare_tools
registry.resolve_tool
registry.list_replacements
registry.list_dependents
registry.report_gap
registry.get_access_projection
registry.get_tool_card
```

## 37.1 Read-only meta-tools for agents

Suitable for MCP exposure:

```text
registry.search_capabilities
registry.describe_tool
registry.compare_tools
registry.list_replacements
registry.explain_unavailability
```

Administrative registry actions should not normally be directly model-callable.

---

# 38. `registry.search_capabilities`

```yaml
name: registry.search_capabilities

description: >
  Search ServiceFabric for tools that can perform a requested capability.
  Use this when the appropriate tool is unknown. It returns concise
  candidate summaries rather than invoking the tools.

inputSchema:
  type: object
  additionalProperties: false
  properties:
    objective:
      type: string
    availableInputs:
      type: array
      items:
        type: string
    desiredOutputs:
      type: array
      items:
        type: string
    maximumEffectClass:
      type: string
    maximumResults:
      type: integer
      minimum: 1
      maximum: 20
      default: 8
  required:
    - objective
```

This is a meta-tool and should remain read-only.

---

# 39. `registry.describe_tool`

```yaml
name: registry.describe_tool

description: >
  Retrieve the callable contract, limitations, effects, permissions,
  and examples for a ServiceFabric tool.

inputSchema:
  type: object
  additionalProperties: false
  properties:
    toolId:
      type: string
    versionConstraint:
      type: string
  required:
    - toolId
```

The result should be caller-specific and omit inaccessible information.

---

# 40. Registry consistency rules

The registry must reject inconsistent publication states.

Examples:

```text
Active ToolRevision
    but no active deployment for required environment

MCP-exposed tool
    but no MCP projection

Tool marked callable
    but maintenance graph quarantined

Revision marked active
    but policy bundle missing

Deprecated tool
    but replacement reference invalid

Retired tool
    still receiving new dependency registrations
```

---

# 41. Registry transactions

Publication and lifecycle changes require atomic transactions.

```typescript
export interface RegistryTransaction {
  transactionId: string;

  operations: RegistryOperation[];

  expectedVersion?: string;
  createdAt: string;
}
```

```typescript
export type RegistryOperation =
  | RegisterToolDefinition
  | PublishToolRevision
  | ActivateRevision
  | RegisterDeployment
  | UpdateLifecycleState
  | RegisterRelationship
  | PublishDeprecationNotice
  | RetireRevision;
```

The registry should support optimistic concurrency.

---

# 42. Caching

Caches may be used for:

* Capability search
* Tool cards
* Access projections
* Contract retrieval
* Revision resolution
* MCP tool listing
* Deployment routing

## 42.1 Cache keys

Include relevant dimensions:

```text
query hash
caller scope fingerprint
tenant
environment
protocol
tool catalogue generation
policy generation
health generation
```

## 42.2 Invalidation triggers

* New tool revision
* Lifecycle change
* Policy change
* Caller-scope change
* Quarantine
* Deployment failure
* Deprecation
* Replacement publication
* Capability-index rebuild

Authorization-sensitive caches must never be shared across incompatible caller contexts.

---

# 43. Registry availability

The registry is critical infrastructure.

A registry outage should not necessarily stop every active invocation.

Recommended strategy:

```text
Primary registry
      ↓
Signed local resolution cache
      ↓
Known active revision and deployment
```

The invocation runtime may use a recent signed resolution cache when:

* Tool and revision are already known.
* Policy decision remains valid.
* Deployment health is known.
* Cache age is within the tool’s tolerance.
* No quarantine revocation is known.

High-risk tools should require fresher registry and policy state.

---

# 44. Signed resolution records

```typescript
export interface SignedResolutionRecord {
  resolution: ToolResolutionResult;

  policyGeneration: string;
  catalogueGeneration: string;
  healthGeneration: string;

  issuedAt: string;
  expiresAt: string;

  signature: string;
}
```

A cached resolution cannot override:

* A known quarantine
* Expired authorization
* Expired approval
* Revoked credentials
* Retired revision
* Data-residency policy

---

# 45. Registry security

Security requirements:

* Mutual authentication between platform services
* Fine-grained administrative permissions
* Immutable revision records
* Signed publication attestations
* Audit logging
* Tenant isolation
* Encrypted sensitive metadata
* No raw secrets in registry records
* Policy references rather than embedded credentials
* Protection against malicious tool descriptions
* Validation of imported external schemas

Tool descriptions and examples are untrusted content from the perspective of the registry user interface and model context.

They must not:

* Grant permissions
* Add hidden tools
* Request secrets
* Override routing
* Alter caller identity
* Suppress warnings

---

# 46. Description integrity

A compromised description can manipulate model tool selection.

Therefore:

* Descriptions must come from signed ToolRevisions.
* Description changes require a new revision.
* External MCP descriptions must be normalized.
* Tool descriptions cannot contain executable instructions unrelated to capability use.
* Descriptions cannot instruct callers to reveal secrets.
* Negative-use guidance must be preserved.
* Description provenance must be auditable.

A security scanner should inspect descriptions for:

* Prompt injection
* Cross-tool manipulation
* Secret requests
* Authorization claims
* Misrepresented effects
* Instructions to suppress evidence

---

# 47. Registry observability

Core metrics:

```text
registry_search_requests_total
registry_search_latency_ms
registry_candidates_evaluated
registry_candidates_returned
registry_authorization_filtered
registry_health_filtered
registry_resolution_requests_total
registry_resolution_failures_total
registry_cache_hit_rate
registry_stale_resolution_uses_total
registry_tool_list_refreshes_total
registry_catalogue_generation
registry_capability_gaps_total
registry_tool_confusion_rate
```

Quality metrics:

```text
registry_selection_precision
registry_selection_recall
registry_top1_success_rate
registry_top3_success_rate
registry_unnecessary_tool_rate
registry_gap_accuracy
registry_replacement_adoption_rate
registry_deprecated_selection_rate
```

---

# 48. Registry evaluations

## 48.1 Discovery precision

Given an objective, are returned tools genuinely useful?

## 48.2 Discovery recall

Does the candidate set contain the best available tool?

## 48.3 Negative selection

Does the registry avoid inappropriate tools?

## 48.4 Effect awareness

Does the registry exclude or penalize tools with excessive effects?

## 48.5 Input compatibility

Does it recognize whether required inputs are available?

## 48.6 Authorization correctness

Does it prevent unauthorized tool exposure?

## 48.7 Lifecycle correctness

Does it avoid retired, quarantined, and incompatible revisions?

## 48.8 Context efficiency

How many tool tokens are required before a correct selection?

---

# 49. Evaluation dataset structure

```typescript
export interface ToolDiscoveryEvaluationCase {
  caseId: string;

  objective: string;
  callerProfile: string;

  availableInputs: string[];
  desiredOutputs: string[];

  requiredToolIds?: string[];
  acceptableToolIds: string[];
  prohibitedToolIds: string[];

  maximumEffectClass?: string;

  expectedGap?: boolean;
}
```

The dataset should include:

* Obvious matches
* Similar-tool ambiguity
* Missing inputs
* Unauthorized capabilities
* Deprecated tools
* Unavailable tools
* Composite versus primitive tools
* Requests requiring no tool
* Requests requiring a new capability

---

# 50. Domain examples

## 50.1 Web development

Request:

```text
Check whether the new page visually matches the reference.
```

Candidates:

```text
web.capture_screenshot
web.compare_visuals
web.run_accessibility_audit
```

Preferred:

```text
web.compare_visuals
```

Reason:

* Produces the desired comparison directly.
* Screenshot capture may remain an internal dependency.

## 50.2 Financial analysis

Request:

```text
Calculate portfolio value at risk using current positions.
```

Candidates:

```text
finance.calculate_var
finance.retrieve_positions
finance.retrieve_market_data
math.calculate
```

The registry may recommend a graph composition if positions and market data are not already available.

## 50.3 Software engineering

Request:

```text
Determine why the test suite fails on the latest commit.
```

Candidates:

```text
software.run_tests
software.inspect_logs
software.investigate_failure
```

Preferred tool depends on desired abstraction:

* `software.run_tests` for raw execution
* `software.investigate_failure` for bounded agent-backed diagnosis

## 50.4 Project management

Request:

```text
Create a task for the unresolved security review.
```

Candidate:

```text
project.create_task
```

The tool card must show:

* Reversible external write
* Approval policy
* Required project identifier

## 50.5 Organisational effectiveness

Request:

```text
Compare workload distribution across country offices.
```

Candidates:

```text
organisation.compare_workloads
organisation.retrieve_staffing_data
organisation.benchmark_units
```

The registry should distinguish data retrieval from comparative analysis.

---

# 51. Declarative registry configuration

```yaml
apiVersion: servicefabric.ai/v1alpha1
kind: ToolRegistryConfiguration

metadata:
  id: primary-tool-registry
  version: 1.0.0

spec:
  indexes:
    exact:
      enabled: true

    keyword:
      enabled: true
      fields:
        - title
        - description
        - concepts
        - aliases
        - examples

    semantic:
      enabled: true
      fields:
        - summary
        - whenToUse
        - whenNotToUse
        - exampleRequests
        - negativeExamples

    relationships:
      enabled: true

  discovery:
    maximumInitialCandidates: 100
    maximumRankedCandidates: 20
    defaultReturnedCandidates: 8

    authorizationFiltering: true
    lifecycleFiltering: true
    healthFiltering: true
    candidateDiversification: true

  resolution:
    preferHighestCompatibleVersion: true
    permitDegradedTools: true
    requireActiveMaintenanceGraph: true
    requirePolicyBundle: true

  caching:
    capabilitySearchTtl: PT5M
    toolCardTtl: PT15M
    accessProjectionTtl: PT2M
    resolutionTtl: PT1M

  federation:
    directExternalExposure: false
    requireWrapperRevision: true
    requireSchemaDriftMonitoring: true
```

---

# 52. Registry service interfaces

```typescript
export interface ToolRegistry {
  searchCapabilities(
    request: CapabilitySearchRequest
  ): Promise<CapabilitySearchResult>;

  describeTool(
    request: DescribeToolRequest
  ): Promise<ToolDescriptionResult>;

  compareTools(
    request: ToolComparisonRequest
  ): Promise<ToolComparisonResult>;

  resolveTool(
    request: ToolResolutionRequest
  ): Promise<ToolResolutionResult>;

  listReplacements(
    toolId: string,
    caller: CallerContext
  ): Promise<ToolReplacement[]>;

  listDependents(
    toolId: string
  ): Promise<ToolDependent[]>;

  publishRevision(
    transaction: PublishRevisionTransaction
  ): Promise<void>;

  updateLifecycle(
    request: LifecycleUpdateRequest
  ): Promise<void>;
}
```

---

# 53. Reference discovery flow

```text
Objective:
    Find recent academic research on agent tool selection.

1. Interpret objective:
     domain = research
     capability = scholarly discovery
     freshness required = true

2. Retrieve candidate capabilities:
     research.scholarship_search
     web.general_search
     research.document_retrieval

3. Retrieve implementing tools:
     research.search_papers
     web.search_pages
     research.retrieve_paper

4. Apply input/output filter:
     retrieve_paper requires known document identifier
     exclude or lower rank

5. Apply authorization:
     caller has research.read and web.read

6. Apply health:
     scholarly search healthy
     web search healthy

7. Rank:
     research.search_papers = 0.95
     web.search_pages = 0.72

8. Return compact cards.

9. Caller selects research.search_papers.

10. Registry returns full invocation contract.

11. Runtime resolves active revision and deployment.
```

---

# 54. Reference resolution flow

```text
Selected:
    research.search_papers
    version constraint ^1.0

Active revisions:
    1.2.4 healthy
    1.3.0 canary
    2.0.0 staging only

Caller:
    assigned to canary experiment

Environment:
    production

Result:
    resolve 1.3.0 canary deployment

Resolution remains fixed for invocation.
```

---

# 55. Reference gap flow

```text
Objective:
    Retrieve and validate private Bloomberg research reports.

Registry search:
    No tool has:
      required private provider access
      required document rights
      required validation output

Nearest tools:
    research.retrieve_document
    research.validate_citation

Gap:
    Provider-specific authenticated retrieval missing.

Recommended action:
    Build new external-provider retrieval tool,
    then compose with citation validation.
```

---

# 56. Registry lifecycle integration

```text
System-Building Graph
    publishes ToolRevision
          ↓
Registry
    indexes capability
          ↓
Maintenance Graph
    updates ToolStatus
          ↓
Registry
    adjusts discovery and resolution
          ↓
Evolution Graph
    publishes replacement
          ↓
Registry
    promotes, deprecates and migrates
```

The registry therefore connects all three lifecycle graphs.

---

# 57. Registry invariants

```text
SF-R001  Every public tool has a stable unique identifier.
SF-R002  Every active tool points to at least one immutable revision.
SF-R003  Every active revision has a valid policy bundle.
SF-R004  Every active revision has a maintenance graph.
SF-R005  Every callable revision has a ready deployment.
SF-R006  Discovery is caller- and tenant-aware.
SF-R007  Hidden tools are never included in model-facing catalogues.
SF-R008  Quarantined tools cannot resolve for new invocations.
SF-R009  Retired tools cannot accept new dependency registrations.
SF-R010  Tool resolution remains stable for an invocation.
SF-R011  Provider variants do not dominate public discovery.
SF-R012  Tool descriptions are signed revision artifacts.
SF-R013  Description metadata cannot grant authorization.
SF-R014  External MCP tools require ServiceFabric normalization.
SF-R015  External annotations do not determine effect classification.
SF-R016  Authorization filtering occurs before model-facing projection.
SF-R017  Health influences routing but is owned by maintenance.
SF-R018  Policy decisions remain owned by the policy service.
SF-R019  Every recommendation includes reason codes.
SF-R020  Every capability gap is explicit rather than silently approximated.
SF-R021  Deprecated tools include replacement guidance where available.
SF-R022  Compatibility adapters cannot weaken authorization or effects.
SF-R023  Every registry mutation is auditable.
SF-R024  Revision publication is atomic.
SF-R025  Administrative registry actions are not generally model-callable.
SF-R026  Discovery caches include authorization context.
SF-R027  Cached resolution cannot override a known quarantine.
SF-R028  Candidate ranking considers input and output compatibility.
SF-R029  Candidate ranking considers effect compatibility.
SF-R030  Tool popularity alone cannot determine ranking.
SF-R031  Similar candidates are diversified before presentation.
SF-R032  Detailed schemas are loaded only after shortlisting.
SF-R033  Graph dependencies resolve to a version lock.
SF-R034  Exact revisions remain available for reproducible workflows.
SF-R035  Dynamic catalogue changes invalidate affected projections.
```

---

# 58. Architectural decision

ServiceFabric should implement tool access as a two-stage process:

```text
DISCOVERY
    What capability should be used?

RESOLUTION
    Which exact revision and deployment should execute it?
```

The complete flow is:

```text
Agent or graph objective
        ↓
Capability search
        ↓
Small authorization-aware candidate set
        ↓
Tool selection
        ↓
Full contract retrieval
        ↓
Revision resolution
        ↓
Deployment routing
        ↓
Canonical invocation pipeline
        ↓
Maintenance-supervised execution
```

This design avoids presenting the model with the entire platform and preserves separation between:

* Capability semantics
* Tool contracts
* Implementation revisions
* Runtime deployments
* Providers
* Authorization
* Operational health

The registry becomes the central map of ServiceFabric, while the Tool Capsule remains the unit of execution and the three lifecycle graphs remain responsible for construction, operation, and improvement.
