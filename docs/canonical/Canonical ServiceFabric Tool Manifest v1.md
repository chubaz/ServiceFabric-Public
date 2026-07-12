# Canonical ServiceFabric Tool Manifest v1

**Status:** Architecture baseline
**API version:** `servicefabric.ai/v1alpha1`
**Primary resource:** `ToolDefinition`
**MCP target version:** `2025-11-25`

## 1. Purpose

The ServiceFabric Tool Manifest is the canonical, protocol-independent description of a capability exposed as a tool.

It must contain enough information for ServiceFabric to:

1. Determine what the tool does.
2. Explain when an agent should and should not call it.
3. Validate its inputs and outputs.
4. Execute it through the appropriate service or graph.
5. control permissions and side effects.
6. Operate its maintenance graph.
7. Evaluate its quality.
8. Observe its execution.
9. Improve it through an evolution graph.
10. Generate a standards-compliant MCP tool definition.

The manifest describes **desired tool behaviour**. Runtime health and deployment observations must be stored separately as `ToolStatus` resources.

---

# 2. Core design rules

## 2.1 ServiceFabric remains protocol-independent

The internal tool contract must not be identical to the MCP contract.

```text
ToolDefinition
      │
      ├── MCP projection
      ├── Internal graph projection
      ├── REST/OpenAPI projection
      ├── Evaluation projection
      └── Deployment configuration
```

MCP is an external interoperability surface. ServiceFabric’s internal representation must be richer and remain usable even when the MCP specification changes.

## 2.2 Desired state and observed state are separate

The authored manifest contains:

* Intended behaviour
* Interface definitions
* Policies
* Graph references
* Reliability requirements
* Evaluation requirements

It must not contain mutable runtime information such as:

* Current health
* Active incident
* Current error rate
* Last invocation
* Current deployed instance
* Provider rate-limit state
* Circuit-breaker state

These belong in a generated `ToolStatus` resource.

## 2.3 Every tool has a bounded capability

A tool should perform one intelligible operation.

Bad boundary:

```text
finance_tool
```

Better boundaries:

```text
finance.get_market_price
finance.retrieve_filing
finance.normalize_statements
finance.calculate_portfolio_risk
finance.run_stress_scenario
```

A graph may compose several narrow tools into a broader capability.

## 2.4 Tool policy is authoritative; MCP annotations are informative

MCP supports hints including:

* `readOnlyHint`
* `destructiveHint`
* `idempotentHint`
* `openWorldHint`

The MCP specification explicitly treats these annotations as untrusted hints. Therefore, ServiceFabric must generate them from internal policy but must never use received MCP annotations as the sole basis for authorization or risk decisions.

## 2.5 Structured outputs are mandatory in ServiceFabric

Although MCP permits unstructured content, every native ServiceFabric tool should define an output schema and return a structured result.

Under the current MCP specification, tools can expose an `outputSchema`; servers must return conforming structured content when one is defined, and clients should validate it.

## 2.6 Tool errors must be recoverable by agents

ServiceFabric distinguishes:

* Protocol errors
* Tool execution errors
* Policy errors
* Infrastructure errors
* Quality-control failures

MCP protocol errors should be reserved for conditions such as an unknown tool or malformed protocol request. Input validation, provider failures, and business-rule failures should normally be returned as tool results with `isError: true`, allowing the calling model or graph to repair its request.

---

# 3. Resource model

ServiceFabric should define four related resources.

```text
ToolDefinition
    Desired capability and policy

ToolRevision
    Immutable built artifact derived from a ToolDefinition

ToolDeployment
    Placement and runtime configuration of a ToolRevision

ToolStatus
    Observed operational and quality state
```

## 3.1 `ToolDefinition`

The source-controlled, human-authored definition.

## 3.2 `ToolRevision`

Created by the system-building graph.

It contains:

* Resolved dependencies
* Generated MCP definition
* Compiled code or container reference
* Policy bundle
* Test results
* Evaluation results
* Content hash
* Supply-chain attestations

A revision is immutable.

## 3.3 `ToolDeployment`

Specifies:

* Environment
* Region
* Runtime
* Replica count
* Network policy
* Secret bindings
* Active revision
* Rollout strategy

## 3.4 `ToolStatus`

Maintained by the system-maintenance graph.

It records:

* Health
* Availability
* Latency
* Error rate
* Quality score
* Circuit-breaker state
* Active provider
* Last successful evaluation
* Current deployed revision
* Incidents and warnings

---

# 4. Canonical manifest structure

```yaml
apiVersion: servicefabric.ai/v1alpha1
kind: ToolDefinition

metadata: {}
spec:
  purpose: {}
  interface: {}
  behavior: {}
  execution: {}
  agenticBacking: {}
  effects: {}
  security: {}
  reliability: {}
  observability: {}
  quality: {}
  lifecycle: {}
  dependencies: {}
  mcp: {}
```

---

# 5. Metadata

```yaml
metadata:
  id: research.search_papers
  version: 1.0.0
  title: Scholarly Paper Search

  description: >
    Searches scholarly sources for papers relevant to a research
    question and returns ranked results with identifiers and provenance.

  owners:
    team: research-services
    technical:
      - user:lorenzo
    business:
      - team:research-platform

  tags:
    - research
    - retrieval
    - scholarly
    - external-data

  labels:
    maturity: beta
    criticality: medium
    domain: research

  createdAt: 2026-07-11
  documentationRef: docs://tools/research.search_papers
```

## 5.1 Identifier convention

The ServiceFabric convention should be:

```text
<domain>.<verb>_<object>
```

Examples:

```text
web.search_pages
weather.get_forecast
research.search_papers
finance.retrieve_filing
finance.calculate_var
software.run_tests
project.create_task
organisation.compare_units
```

Rules:

* Lowercase
* Stable after publication
* No implementation or provider name
* No version in the identifier
* Prefer explicit verbs
* Maximum 64 characters for direct MCP compatibility

MCP tool names should be 1–64 characters and may use ASCII letters, digits, underscores, dashes, dots, and forward slashes.

Provider-specific variants belong in routing configuration:

```yaml
providers:
  - arxiv
  - crossref
  - semantic-scholar
```

They should not produce separate public tools unless their semantics materially differ.

---

# 6. Purpose and agent-selection semantics

The `purpose` section exists primarily to improve tool selection.

```yaml
spec:
  purpose:
    summary: >
      Discover scholarly papers relevant to a research question.

    capabilities:
      - Search scholarly indexes.
      - Filter by publication date.
      - Rank results by semantic relevance.
      - Return stable identifiers when available.
      - Report the source through which each record was discovered.

    whenToUse:
      - The user asks for scholarly or academic literature.
      - A graph needs papers supporting or challenging a claim.
      - A research workflow needs DOI or arXiv identifiers.
      - Current literature must be discovered before analysis.

    whenNotToUse:
      - The caller already has a known DOI and only needs its metadata.
      - The caller requires general web pages rather than scholarship.
      - The caller needs the complete text of a known paper.
      - The task is to verify that a quotation appears in a paper.

    prerequisites:
      - The query must describe a research subject or question.

    expectedCallers:
      - research-agent
      - literature-review-graph
      - learning-agent
      - financial-research-agent

    invocationExamples:
      - intent: Find recent papers about LLM tool selection.
        arguments:
          query: tool selection in large language model agents
          publishedAfter: 2024-01-01
          maximumResults: 20
```

This information should be used to generate a concise MCP `description`, but it should remain available in richer form to internal ServiceFabric graphs.

---

# 7. Interface

## 7.1 Input schema

```yaml
spec:
  interface:
    inputSchema:
      $schema: https://json-schema.org/draft/2020-12/schema
      type: object
      additionalProperties: false

      properties:
        query:
          type: string
          minLength: 3
          maxLength: 2000
          description: >
            Research question, topic, title fragment, or keyword query.

        publishedAfter:
          type: string
          format: date
          description: Earliest acceptable publication date.

        publishedBefore:
          type: string
          format: date
          description: Latest acceptable publication date.

        maximumResults:
          type: integer
          minimum: 1
          maximum: 100
          default: 20

        sources:
          type: array
          uniqueItems: true
          items:
            type: string
            enum:
              - auto
              - arxiv
              - crossref
              - semantic-scholar
          default:
            - auto

      required:
        - query
```

Design rules:

* Use `additionalProperties: false` unless extensibility is intentional.
* Every property requires a meaningful description.
* Express constraints in the schema rather than only in prose.
* Do not expose secrets, internal provider identifiers, or routing controls.
* Avoid polymorphic inputs until they materially improve usability.
* Defaults must be safe.
* Inputs should represent caller intent, not implementation mechanics.

## 7.2 Standard output envelope

Every ServiceFabric tool should return an object with this conceptual shape:

```yaml
status: success | partial | error
data: {}
error: {}
warnings: []
evidence: []
meta: {}
```

A tool-specific output schema expands the `data` property.

```yaml
spec:
  interface:
    outputSchema:
      $schema: https://json-schema.org/draft/2020-12/schema
      type: object
      additionalProperties: false

      properties:
        status:
          type: string
          enum:
            - success
            - partial
            - error

        data:
          type:
            - object
            - "null"

        error:
          type:
            - object
            - "null"
          properties:
            code:
              type: string
            category:
              type: string
              enum:
                - validation
                - authorization
                - dependency
                - timeout
                - rate_limit
                - business_rule
                - quality
                - internal
            message:
              type: string
            retryable:
              type: boolean
            suggestedAction:
              type:
                - string
                - "null"
            details:
              type: object
          required:
            - code
            - category
            - message
            - retryable

        warnings:
          type: array
          items:
            type: object
            properties:
              code:
                type: string
              message:
                type: string
            required:
              - code
              - message

        evidence:
          type: array
          items:
            type: object
            properties:
              type:
                type: string
              source:
                type: string
              locator:
                type:
                  - string
                  - "null"
              retrievedAt:
                type:
                  - string
                  - "null"
                format: date-time
            required:
              - type
              - source

        meta:
          type: object
          properties:
            invocationId:
              type: string
            toolId:
              type: string
            toolVersion:
              type: string
            durationMs:
              type: integer
            provider:
              type:
                - string
                - "null"
            cached:
              type: boolean
          required:
            - invocationId
            - toolId
            - toolVersion

      required:
        - status
        - data
        - error
        - warnings
        - evidence
        - meta
```

## 7.3 Tool-specific data schema

For `research.search_papers`:

```yaml
data:
  type: object
  properties:
    results:
      type: array
      items:
        type: object
        properties:
          title:
            type: string
          authors:
            type: array
            items:
              type: string
          abstract:
            type:
              - string
              - "null"
          publicationDate:
            type:
              - string
              - "null"
            format: date
          doi:
            type:
              - string
              - "null"
          arxivId:
            type:
              - string
              - "null"
          sourceUrl:
            type:
              - string
              - "null"
            format: uri
          discoverySource:
            type: string
          relevanceScore:
            type:
              - number
              - "null"
            minimum: 0
            maximum: 1
        required:
          - title
          - authors
          - discoverySource

    totalReturned:
      type: integer

    queryInterpretation:
      type: object
      properties:
        normalizedQuery:
          type: string
        concepts:
          type: array
          items:
            type: string

  required:
    - results
    - totalReturned
    - queryInterpretation
```

## 7.4 Content projection

The ServiceFabric MCP adapter should normally return both:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Found 12 potentially relevant scholarly papers."
    }
  ],
  "structuredContent": {
    "status": "success",
    "data": {},
    "error": null,
    "warnings": [],
    "evidence": [],
    "meta": {}
  },
  "isError": false
}
```

The text content should be short and human-readable. The structured result is authoritative for downstream graphs.

---

# 8. Behaviour classification

```yaml
spec:
  behavior:
    capabilityClass: retrieval

    determinism: probabilistic
    statefulness: stateless
    interactionMode: request_response

    freshness:
      sensitive: true
      maximumAcceptableAge: P1D

    latencyClass: interactive
    expectedDuration:
      typicalMs: 3000
      maximumMs: 20000

    longRunning: false
    supportsCancellation: true
    supportsProgress: false

    cache:
      allowed: true
      defaultTtl: PT6H
      keyFields:
        - query
        - publishedAfter
        - publishedBefore
        - maximumResults
        - sources
```

Recommended values:

### `capabilityClass`

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
meta
```

### `determinism`

```text
deterministic
provider_dependent
probabilistic
agentic
```

### `statefulness`

```text
stateless
session_stateful
persistent_stateful
```

### `interactionMode`

```text
request_response
streaming
long_running
event_driven
```

---

# 9. Execution

```yaml
spec:
  execution:
    adapter: native_service

    target:
      service: research-search-service
      operation: searchPapers
      protocol: http
      endpointRef: service://research-search-service/search

    timeout:
      soft: PT15S
      hard: PT20S

    concurrency:
      maximumPerInstance: 20
      queueLimit: 100

    retries:
      maximumAttempts: 3
      retryOn:
        - connection_failure
        - provider_5xx
        - provider_timeout
        - rate_limit
      neverRetryOn:
        - invalid_input
        - authorization_failure
        - policy_denial

      backoff:
        strategy: exponential_jitter
        initialDelay: PT0.5S
        maximumDelay: PT4S

    idempotency:
      classification: naturally_idempotent
      idempotencyKeyRequired: false
```

Supported adapters should include:

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

A public tool should not reveal the adapter or provider to the calling model unless it affects the tool’s semantics.

---

# 10. Agentic backing

```yaml
spec:
  agenticBacking:
    level: assisted

    maintenanceGraphRef:
      name: research-search-maintenance
      versionConstraint: "^1.0"

    responsibilities:
      - normalize_query
      - select_providers
      - retry_transient_failures
      - merge_results
      - remove_duplicates
      - rank_results
      - validate_identifiers
      - attach_provenance
      - assess_partial_success

    modelUse:
      permitted: true
      purposes:
        - query_reformulation
        - relevance_ranking
      prohibitedPurposes:
        - inventing_citations
        - generating_missing_identifiers

    internalToolAccess:
      allowed:
        - research.query_arxiv
        - research.query_crossref
        - research.query_semantic_scholar
        - research.validate_doi

      denied:
        - filesystem.write
        - email.send
        - deployment.modify

    limits:
      maximumInternalToolCalls: 8
      maximumModelCalls: 2
      maximumTokens: 8000
      maximumCostUsd: 0.10

    completionPolicy:
      permitPartialResults: true
      minimumValidResults: 1
      evidenceRequired: true
```

## 10.1 Agentic-backing levels

```text
none
guarded
assisted
agentic
autonomous
```

### None

Direct deterministic execution.

Example:

```text
math.calculate
```

### Guarded

Validation, normalization, retries, and output checking.

Example:

```text
weather.get_forecast
```

### Assisted

Limited reasoning around an otherwise bounded operation.

Example:

```text
research.search_papers
```

### Agentic

The backing graph plans and performs several internal operations.

Example:

```text
software.investigate_failure
```

### Autonomous

The backing graph can monitor, plan, act, and revisit its work under explicit governance.

Example:

```text
project.manage_delivery_risks
```

Autonomous backing should be exceptional rather than the default.

---

# 11. Effects and reversibility

```yaml
spec:
  effects:
    class: read_external

    reads:
      - public_scholarly_metadata

    writes: []

    persistentMutation: false
    externalCommunication: false
    financialEffect: false
    codeExecution: false

    destructive: false
    reversible: true
    idempotent: true
    openWorld: true
```

## 11.1 Effect classes

```text
pure
read_internal
read_external
write_reversible
write_irreversible
execute_code
communicate_external
financial_transaction
administrative_control
```

## 11.2 Approval policy

Approval belongs in the security section, but it is derived partly from effects.

Suggested defaults:

| Effect                   | Default approval       |
| ------------------------ | ---------------------- |
| Pure computation         | None                   |
| Internal read            | Policy-based           |
| External public read     | None                   |
| Reversible write         | Policy-based           |
| Irreversible write       | Always                 |
| External communication   | Always                 |
| Financial transaction    | Always                 |
| Arbitrary code execution | Always or sandbox-only |
| Administrative control   | Always                 |

---

# 12. Security and governance

```yaml
spec:
  security:
    authentication:
      required: true
      acceptedPrincipals:
        - user
        - service
        - agent

    authorization:
      requiredScopes:
        - research.read

      policyRef: policy://research/search-papers

    approval:
      mode: policy
      policyRef: policy://approvals/read-public-data

    data:
      inputClassification:
        maximum: internal

      outputClassification:
        maximum: public

      personalData:
        permitted: false

      confidentialData:
        permitted: false

      retention:
        arguments: P7D
        results: P1D
        audit: P365D

    secrets:
      bindings:
        - scholarly-provider-credentials
      exposeToCaller: false
      exposeToModel: false

    network:
      egress:
        mode: allowlist
        destinations:
          - arxiv.org
          - api.crossref.org
          - api.semanticscholar.org

      ingress:
        mode: servicefabric_only

    sandbox:
      required: false

    promptInjection:
      externalContentIsUntrusted: true
      contentMayNotModifyPolicy: true
      contentMayNotAuthorizeToolCalls: true
```

Security policy should be enforced outside the tool implementation as well as within it.

No tool description, prompt, returned webpage, document, MCP annotation, or internal model response may override:

* Authorization
* Approval requirements
* Data-classification rules
* Network policy
* Tool-call budgets
* Prohibited actions

---

# 13. Reliability

```yaml
spec:
  reliability:
    serviceLevel:
      availabilityTarget: 0.995
      p95LatencyMs: 8000
      maximumErrorRate: 0.02

    circuitBreaker:
      enabled: true
      failureThreshold: 5
      observationWindow: PT1M
      openDuration: PT30S

    fallback:
      strategy: provider_sequence
      providers:
        - semantic-scholar
        - crossref
        - arxiv

      permitDegradedResult: true

    bulkhead:
      enabled: true
      pool: external-research

    overload:
      strategy: reject
      retryAfter: PT10S

    dependencyFailure:
      returnPartialResults: true
      exposeDependencyDetails: false
```

The maintenance graph must use this section rather than invent retry or fallback behaviour at runtime.

---

# 14. Observability

```yaml
spec:
  observability:
    tracing:
      enabled: true
      propagateContext: true

    logging:
      enabled: true
      arguments: redacted
      resultContent: metadata_only
      providerPayloads: false

    metrics:
      - invocation_count
      - success_rate
      - partial_success_rate
      - error_rate
      - latency_ms
      - provider_latency_ms
      - result_count
      - duplicate_rate
      - identifier_validity_rate
      - estimated_cost

    audit:
      enabled: true
      record:
        - caller
        - tool_revision
        - policy_decision
        - provider_selection
        - side_effect_class
        - result_status

    correlation:
      invocationIdRequired: true
      parentGraphRunIdSupported: true
```

A tool invocation should be traceable through:

```text
external graph
    → MCP gateway
        → policy decision
            → maintenance graph
                → service
                    → provider
```

---

# 15. Quality and evaluations

```yaml
spec:
  quality:
    evaluationSuiteRef:
      name: research-search-evaluations
      versionConstraint: "^1.0"

    publicationGates:
      required:
        - schema_validation
        - contract_tests
        - security_tests
        - agent_callability_tests
        - regression_tests
        - provider_failure_tests

    thresholds:
      argumentValidityRate: 0.99
      structuredOutputValidityRate: 1.0
      identifierValidityRate: 0.98
      minimumRelevantResultRate: 0.80
      maximumHallucinatedCitationRate: 0.0

    provenance:
      required: true
      minimumCoverage: 1.0

    testCases:
      normal: 30
      boundary: 15
      adversarial: 20
      failure: 20

    review:
      humanReviewRequiredForMajorVersion: true
      reviewInterval: P90D
```

## 15.1 Agent-callability evaluation

The test suite must evaluate more than whether the service technically works.

It should test whether agents can:

* Select the tool for appropriate requests.
* Avoid it for inappropriate requests.
* Construct valid arguments.
* Interpret its output.
* Recover from its errors.
* Distinguish partial results from complete results.
* Respect side-effect and approval requirements.
* Compose it with other tools.

A technically correct tool with a poor description or confusing schema is not production-ready.

---

# 16. Lifecycle graphs

```yaml
spec:
  lifecycle:
    building:
      graphRef:
        name: standard-tool-building
        versionConstraint: "^1.0"

      requiredOutputs:
        - implementation
        - mcp_projection
        - tests
        - evaluation_report
        - policy_bundle
        - documentation
        - deployment_artifact
        - software_bill_of_materials

    evolution:
      graphRef:
        name: standard-tool-evolution
        versionConstraint: "^1.0"

      triggers:
        - type: quality_threshold_breach
        - type: repeated_invalid_calls
          threshold: 20
          window: P7D
        - type: dependency_deprecation
        - type: provider_schema_change
        - type: security_advisory
        - type: manual_request
        - type: recurring_composition_pattern

      permittedChanges:
        patch:
          - descriptions
          - implementation
          - provider_routing
          - retry_policy
          - nonbreaking_schema_constraints

        minor:
          - optional_inputs
          - optional_outputs
          - new_provider
          - new_fallback

        major:
          - required_inputs
          - output_semantics
          - side_effect_class
          - authorization_model

    maintenance:
      graphRef:
        name: research-search-maintenance
        versionConstraint: "^1.0"

      invocationMode: every_call

      responsibilities:
        before:
          - authenticate
          - authorize
          - validate_arguments
          - assess_policy
          - choose_provider
          - establish_budgets

        during:
          - monitor_timeout
          - process_progress
          - handle_transient_failures
          - enforce_call_limits

        after:
          - validate_output
          - attach_provenance
          - classify_completion
          - record_telemetry
          - update_tool_status
```

The same manifest therefore drives all three graph families:

```text
Building graph:
    reads desired specification
    produces a deployable revision

Maintenance graph:
    reads operational policies
    supports each invocation
    updates observed status

Evolution graph:
    reads definition, status, telemetry and evaluations
    proposes or creates a new definition version
```

---

# 17. Dependencies

```yaml
spec:
  dependencies:
    tools:
      - id: research.query_arxiv
        versionConstraint: "^1.0"
        required: false

      - id: research.query_crossref
        versionConstraint: "^1.0"
        required: false

      - id: research.validate_doi
        versionConstraint: "^1.0"
        required: true

    services:
      - id: research-search-service
        versionConstraint: "^2.0"

    models:
      - capability: semantic_ranking
        providerIndependent: true
        minimumContextTokens: 8000

    data:
      - id: provider-routing-config
        required: true

    policies:
      - policy://research/search-papers
      - policy://approvals/read-public-data
```

Dependency references should express capabilities rather than hard-code providers wherever possible.

For example:

```yaml
models:
  - capability: semantic_ranking
```

is preferable to:

```yaml
models:
  - model: provider-specific-model-name
```

The runtime router should resolve the actual implementation.

---

# 18. MCP projection

```yaml
spec:
  mcp:
    expose: true
    protocolVersion: "2025-11-25"

    name: research.search_papers
    title: Scholarly Paper Search

    descriptionTemplate: >
      Search scholarly sources for papers relevant to a research
      question. Use this for academic literature discovery and DOI or
      arXiv identification. Do not use it to retrieve the full text of a
      known paper or to verify quotations.

    annotations:
      readOnlyHint: true
      destructiveHint: false
      idempotentHint: true
      openWorldHint: true

    execution:
      taskSupport: forbidden

    result:
      returnStructuredContent: true
      returnTextSummary: true
      useIsErrorForExecutionFailures: true

    metadata:
      expose:
        - tool_id
        - tool_version
        - capability_class
        - risk_level

      hide:
        - internal_endpoint
        - provider_credentials
        - network_policy
        - model_configuration
        - internal_fallback_order
```

The current MCP version is `2025-11-25`, with protocol version agreement performed during connection initialization. Optional features can only be used when successfully negotiated.

The generated MCP descriptor would resemble:

```json
{
  "name": "research.search_papers",
  "title": "Scholarly Paper Search",
  "description": "Search scholarly sources for papers relevant to a research question. Use this for academic literature discovery and DOI or arXiv identification. Do not use it to retrieve the full text of a known paper or to verify quotations.",
  "inputSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "query": {
        "type": "string",
        "minLength": 3,
        "maxLength": 2000
      },
      "publishedAfter": {
        "type": "string",
        "format": "date"
      },
      "publishedBefore": {
        "type": "string",
        "format": "date"
      },
      "maximumResults": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 20
      },
      "sources": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "auto",
            "arxiv",
            "crossref",
            "semantic-scholar"
          ]
        }
      }
    },
    "required": [
      "query"
    ]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "enum": [
          "success",
          "partial",
          "error"
        ]
      },
      "data": {
        "type": [
          "object",
          "null"
        ]
      },
      "error": {
        "type": [
          "object",
          "null"
        ]
      },
      "warnings": {
        "type": "array"
      },
      "evidence": {
        "type": "array"
      },
      "meta": {
        "type": "object"
      }
    },
    "required": [
      "status",
      "data",
      "error",
      "warnings",
      "evidence",
      "meta"
    ]
  },
  "annotations": {
    "readOnlyHint": true,
    "destructiveHint": false,
    "idempotentHint": true,
    "openWorldHint": true
  },
  "execution": {
    "taskSupport": "forbidden"
  },
  "_meta": {
    "io.servicefabric/tool-id": "research.search_papers",
    "io.servicefabric/tool-version": "1.0.0",
    "io.servicefabric/capability-class": "retrieval",
    "io.servicefabric/risk-level": "medium"
  }
}
```

MCP `tools/list` exposes the tool descriptor, while `tools/call` invokes the named tool with arguments. Servers may advertise `listChanged` support when the available tool set can change.

---

# 19. Tool execution result classification

## 19.1 Success

```json
{
  "status": "success",
  "data": {
    "results": []
  },
  "error": null,
  "warnings": [],
  "evidence": [],
  "meta": {}
}
```

MCP:

```json
{
  "isError": false
}
```

## 19.2 Partial success

```json
{
  "status": "partial",
  "data": {
    "results": []
  },
  "error": null,
  "warnings": [
    {
      "code": "PROVIDER_UNAVAILABLE",
      "message": "One of three configured providers was unavailable."
    }
  ],
  "evidence": [],
  "meta": {}
}
```

MCP:

```json
{
  "isError": false
}
```

A partial result is not necessarily an execution error.

## 19.3 Recoverable execution error

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_DATE_RANGE",
    "category": "validation",
    "message": "publishedAfter must precede publishedBefore.",
    "retryable": true,
    "suggestedAction": "Reverse or correct the date boundaries.",
    "details": {}
  },
  "warnings": [],
  "evidence": [],
  "meta": {}
}
```

MCP:

```json
{
  "isError": true
}
```

## 19.4 Protocol error

Use a JSON-RPC error only when the request cannot be treated as a valid tool execution, such as:

* Unknown tool name
* Malformed JSON-RPC message
* Unsupported method
* Tool calling not supported
* Internal MCP server failure before invocation can be established

---

# 20. Versioning

Tool definitions use semantic versioning:

```text
MAJOR.MINOR.PATCH
```

## Patch

No caller-visible semantic change.

Examples:

* Bug fix
* Description improvement
* Performance improvement
* Provider replacement
* Retry adjustment
* Internal prompt improvement that preserves expected behaviour

## Minor

Backward-compatible capability expansion.

Examples:

* New optional input
* New optional output
* Additional provider
* New supported filter
* Better evidence metadata

## Major

Caller-visible incompatibility or risk change.

Examples:

* New required field
* Removed output field
* Changed output meaning
* Tool becomes stateful
* Tool gains write effects
* Authorization model changes
* Error semantics change materially

The system-evolution graph must not silently introduce a major change.

---

# 21. Tool lifecycle state machine

```text
draft
  ↓
validated
  ↓
built
  ↓
evaluated
  ↓
approved
  ↓
published
  ↓
deployed
  ↓
active
  ├── degraded
  ├── quarantined
  ├── deprecated
  └── retired
```

## Quarantine conditions

A tool should be automatically eligible for quarantine when:

* Output schema validity falls below the required threshold.
* Unauthorized side effects are detected.
* Provenance requirements are violated.
* A critical dependency is compromised.
* The tool repeatedly returns fabricated evidence.
* Error rate exceeds its maximum for a sustained interval.
* Its runtime behaviour differs from its declared effect class.
* A security policy cannot be enforced.

A quarantined tool should either:

* Disappear from external tool discovery, or
* Remain visible but reject calls with a structured availability error

The exact approach should depend on whether callers need to understand that the capability exists but is temporarily unavailable.

---

# 22. Validation and publication gates

A `ToolDefinition` cannot become active until it passes seven gates.

## Gate 1 — Manifest validity

* Correct API version
* Required fields present
* Valid tool identifier
* Valid semantic version
* Valid references

## Gate 2 — Contract validity

* Valid input schema
* Valid output schema
* No secret-bearing inputs
* No ambiguous required fields
* Structured error support

## Gate 3 — Behavioural consistency

Examples:

* `effects.destructive: true` cannot coexist with `readOnlyHint: true`.
* A state-changing tool cannot claim natural idempotency without justification.
* An open-web search tool cannot declare `openWorld: false`.
* A persistent write requires an approval policy.
* A tool marked deterministic cannot depend on unconstrained model output.

## Gate 4 — Security validity

* Required scopes defined
* Network policy defined
* Secrets bound
* Data classification defined
* Approval requirements derived
* Prompt-injection controls present for untrusted content

## Gate 5 — Implementation validity

* Target service exists
* Operation exists
* Dependency versions resolve
* Health endpoint responds
* Cancellation and timeout behaviour are implemented

## Gate 6 — Evaluation validity

* Contract tests pass
* Agent-selection tests pass
* Error-recovery tests pass
* Security tests pass
* Quality thresholds pass

## Gate 7 — MCP conformance

* Generated tool can be listed.
* Inputs can be called through MCP.
* Outputs conform to `outputSchema`.
* Tool execution errors use `isError`.
* Protocol negotiation succeeds.
* Unsupported optional capabilities are not used.

---

# 23. ToolDefinition invariants

The following should become machine-enforced ServiceFabric invariants:

```text
SF-T001  Every tool has a stable unique identifier.
SF-T002  Every tool has an explicit owner.
SF-T003  Every tool defines when it should not be used.
SF-T004  Every tool rejects undeclared inputs by default.
SF-T005  Every native tool defines structured output.
SF-T006  Every execution error has a stable error code.
SF-T007  Every external-data tool defines provenance policy.
SF-T008  Every state-changing tool defines approval policy.
SF-T009  Every tool defines timeout behaviour.
SF-T010  Every retrying tool declares retryable failure classes.
SF-T011  Every agent-backed tool defines call and cost budgets.
SF-T012  Every tool has a maintenance graph.
SF-T013  Every production tool has an evaluation suite.
SF-T014  MCP annotations must be generated from internal effects.
SF-T015  Internal policy cannot be weakened by MCP metadata.
SF-T016  Runtime status cannot mutate the authored definition.
SF-T017  Every published revision is immutable.
SF-T018  Major semantic changes require a major version.
SF-T019  Untrusted content cannot grant permissions.
SF-T020  Every invocation receives a correlation identifier.
```

---

# 24. Minimal valid manifest

A simple deterministic tool should not require the full complexity of the scholarly-search example.

```yaml
apiVersion: servicefabric.ai/v1alpha1
kind: ToolDefinition

metadata:
  id: math.calculate
  version: 1.0.0
  title: Mathematical Calculator
  description: Evaluate a bounded mathematical expression.
  owners:
    team: core-tools

spec:
  purpose:
    summary: Perform deterministic mathematical calculations.
    whenToUse:
      - Exact arithmetic or mathematical evaluation is required.
    whenNotToUse:
      - The task requires financial market data.
      - The task requires symbolic proof.

  interface:
    inputSchema:
      type: object
      additionalProperties: false
      properties:
        expression:
          type: string
      required:
        - expression

    outputSchema:
      type: object
      properties:
        status:
          type: string
        data:
          type: object
        error:
          type:
            - object
            - "null"
        warnings:
          type: array
        evidence:
          type: array
        meta:
          type: object
      required:
        - status
        - data
        - error
        - warnings
        - evidence
        - meta

  behavior:
    capabilityClass: computation
    determinism: deterministic
    statefulness: stateless
    interactionMode: request_response

  execution:
    adapter: native_function
    target:
      service: core-math-service
      operation: calculate
    timeout:
      hard: PT2S

  agenticBacking:
    level: guarded
    maintenanceGraphRef:
      name: deterministic-tool-maintenance
      versionConstraint: "^1.0"
    modelUse:
      permitted: false

  effects:
    class: pure
    destructive: false
    reversible: true
    idempotent: true
    openWorld: false

  security:
    authorization:
      requiredScopes:
        - tools.calculate

  reliability:
    serviceLevel:
      availabilityTarget: 0.9999
      p95LatencyMs: 100

  observability:
    tracing:
      enabled: true
    metrics:
      - invocation_count
      - latency_ms
      - error_rate

  quality:
    evaluationSuiteRef:
      name: math-calculator-evaluations
      versionConstraint: "^1.0"

  lifecycle:
    building:
      graphRef:
        name: standard-tool-building
        versionConstraint: "^1.0"
    evolution:
      graphRef:
        name: standard-tool-evolution
        versionConstraint: "^1.0"
    maintenance:
      graphRef:
        name: deterministic-tool-maintenance
        versionConstraint: "^1.0"

  mcp:
    expose: true
    protocolVersion: "2025-11-25"
    name: math.calculate
    annotations:
      readOnlyHint: true
      destructiveHint: false
      idempotentHint: true
      openWorldHint: false
    execution:
      taskSupport: forbidden
```

---

# 25. Architectural decision

ServiceFabric should adopt the following foundational pattern:

```text
Canonical ToolDefinition
          │
          ▼
System-Building Graph
          │
          ▼
Immutable ToolRevision
          │
          ├── service implementation
          ├── MCP projection
          ├── policy bundle
          ├── evaluation suite
          └── deployment artifact
                    │
                    ▼
              ToolDeployment
                    │
                    ▼
          System-Maintenance Graph
                    │
                    ├── executes and supports calls
                    ├── applies policies
                    ├── validates outputs
                    └── writes ToolStatus
                              │
                              ▼
                    System-Evolution Graph
                              │
                              └── proposes next ToolDefinition version
```

This makes the manifest the central contract connecting tool construction, operation, improvement, governance, and external agent use.
