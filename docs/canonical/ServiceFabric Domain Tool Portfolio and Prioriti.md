# ServiceFabric Domain Tool Portfolio and Prioritisation Framework v1

**Status:** Architecture baseline
**Subsystem:** Capability portfolio management
**API version:** `servicefabric.ai/v1alpha1`
**Primary objective:** Determine which tools ServiceFabric should build, federate, compose, and evolve first.

---

# 1. Purpose

The ServiceFabric tool portfolio should provide agents with a coherent set of capabilities across:

* Web development
* Financial analysis
* Software engineering
* Research
* Learning
* Project management
* Productivity
* Organisational effectiveness
* Management

The portfolio must avoid two common failures:

```text
Too few tools
    Agents lack access to evidence, computation, state and action.

Too many poorly differentiated tools
    Agents select incorrectly, waste context and create unsafe effects.
```

The objective is therefore not to maximize tool count.

It is to maximize:

```text
Useful objectives completed
───────────────────────────
tool complexity + risk + cost
```

---

# 2. Portfolio architecture

ServiceFabric should organize tools into five layers.

```text
Layer 0 — Platform and governance tools
    Discover, inspect, authorize, observe and maintain tools.

Layer 1 — Universal primitives
    Retrieve, calculate, transform, store and execute.

Layer 2 — Domain primitives
    Perform bounded operations in a professional domain.

Layer 3 — Composite tools
    Combine stable primitive sequences into one bounded capability.

Layer 4 — Agent-backed services
    Perform constrained investigation, planning or analysis.
```

## 2.1 Layer 0 — Platform tools

Examples:

```text
registry.search_capabilities
registry.describe_tool
registry.compare_tools
registry.resolve_tool

policy.explain_decision
approval.create_preview
approval.verify

operations.get_tool_health
operations.get_provider_health
operations.report_tool_failure

evaluations.run_suite
evaluations.compare_revisions

graphs.inspect_run
graphs.explain_failure
```

These tools allow agents and operators to understand the ServiceFabric environment itself.

## 2.2 Layer 1 — Universal primitives

Examples:

```text
math.calculate
http.request
web.search_pages
web.retrieve_page
documents.extract_text
data.query_table
data.transform_table
files.read
files.write
code.run
time.get_current
weather.get_forecast
```

These are useful across many domains and should expose narrow, predictable contracts.

## 2.3 Layer 2 — Domain primitives

Examples:

```text
research.search_papers
finance.retrieve_filing
software.run_tests
project.create_task
organisation.retrieve_workforce_metrics
```

These understand domain concepts but still perform one bounded operation.

## 2.4 Layer 3 — Composite tools

Examples:

```text
research.build_evidence_set
finance.build_company_dataset
software.validate_change
project.prepare_status_report
organisation.compare_units
```

A composite hides a recurring, stable sequence of primitives.

## 2.5 Layer 4 — Agent-backed services

Examples:

```text
research.investigate_question
finance.analyse_company
software.investigate_failure
project.assess_delivery_risk
organisation.diagnose_operating_model
```

These require planning, iteration or interpretation but remain bounded by explicit inputs, outputs, budgets and stopping criteria.

---

# 3. Portfolio design principles

## 3.1 Primitives before agents

Before building `finance.analyse_company`, ServiceFabric should have reliable tools for:

* Filing retrieval
* Market-data retrieval
* Financial-statement normalization
* Calculation
* Time-series alignment
* Evidence generation
* Report construction

Otherwise, the high-level tool becomes a large prompt wrapped around unreliable data access.

## 3.2 Read before write

For each domain, build in this order:

```text
Discover
    ↓
Read
    ↓
Analyse
    ↓
Prepare proposed action
    ↓
Approve
    ↓
Commit action
    ↓
Verify effect
```

Example:

```text
project.search_tasks
project.get_task
project.assess_task
project.prepare_task
project.create_task
project.verify_task
```

## 3.3 Exact computation before model inference

Use deterministic implementations for:

* Arithmetic
* Dates
* Statistics
* Financial formulas
* Data validation
* Schema checks
* Identifiers
* Limits
* Reconciliation

Models should interpret or explain calculations, not replace them.

## 3.4 Retrieval and verification remain separate

Examples:

```text
research.search_papers
    Discovers records.

research.retrieve_paper
    Retrieves a known record.

research.validate_citation
    Verifies bibliographic identity.

research.verify_quotation
    Checks whether wording appears in a source.
```

Combining all four into one generic research tool reduces precision and makes evidence quality difficult to evaluate.

## 3.5 Preparation and commitment remain separate

Examples:

```text
communication.prepare_email
communication.send_email

finance.prepare_transaction
finance.submit_transaction

software.prepare_change
software.apply_change

project.prepare_task
project.create_task
```

The preparation result becomes the action preview used for approval.

## 3.6 Public capabilities should be provider-independent

External agents should call:

```text
research.search_papers
```

not:

```text
arxiv.search
crossref.search
semantic_scholar.search
```

Provider-specific tools may remain internal dependencies.

## 3.7 Tool count should be minimized at the model boundary

ServiceFabric may contain hundreds of internal operations while exposing only a small, context-relevant catalogue to a given graph.

---

# 4. Tool prioritisation model

Each proposed tool should receive a portfolio score.

```typescript
export interface ToolPortfolioScore {
  objectiveCoverage: number;
  crossDomainReuse: number;
  compositionalValue: number;
  determinismValue: number;
  evidenceValue: number;
  automationValue: number;

  implementationFeasibility: number;
  providerMaturity: number;

  securityRisk: number;
  effectRisk: number;
  maintenanceBurden: number;
  expectedCost: number;
  catalogueComplexity: number;
}
```

Illustrative formula:

```text
priority score =

    0.18 × objective coverage
  + 0.16 × compositional value
  + 0.14 × cross-domain reuse
  + 0.10 × evidence value
  + 0.10 × automation value
  + 0.08 × determinism value
  + 0.08 × implementation feasibility
  + 0.06 × provider maturity

  - 0.04 × security risk
  - 0.02 × effect risk
  - 0.02 × maintenance burden
  - 0.01 × expected cost
  - 0.01 × catalogue complexity
```

The precise weights may vary by portfolio phase.

During ServiceFabric’s foundation phase, emphasize:

```text
Compositional value
Cross-domain reuse
Determinism
Observability
Low effect risk
```

During domain expansion, emphasize:

```text
Objective coverage
Evidence quality
Domain accuracy
Automation value
```

---

# 5. Priority classes

## P0 — Platform-critical

ServiceFabric cannot operate coherently without it.

## P1 — Foundational

Supports many graphs and enables higher-level tools.

## P2 — Domain-expanding

Adds substantial value within one or more domains.

## P3 — Advanced composite

Automates a recurring multi-tool operation.

## P4 — Governed action

Produces external or persistent effects.

## Experimental

Potentially useful but insufficiently mature, differentiated or governable.

---

# 6. Build, federate or compose decision

For every capability, ServiceFabric should choose among:

```text
BUILD
    Implement a native ServiceFabric capability.

FEDERATE
    Wrap an external MCP server.

ADAPT
    Wrap an external REST, database or vendor API.

COMPOSE
    Build a graph over existing ServiceFabric tools.

REJECT
    Do not expose the capability.
```

## 6.1 Build natively when

* The capability is central to ServiceFabric.
* A stable internal semantic contract is required.
* Several providers may be interchangeable.
* Strong governance or evidence is necessary.
* Domain-specific logic creates substantial value.
* Provider APIs are too granular or unstable.
* Exact reproducibility is required.

## 6.2 Federate when

* A maintained MCP server already exposes the capability.
* The provider is authoritative.
* Tool semantics are sufficiently stable.
* Authentication can be isolated.
* ServiceFabric can revalidate contracts and outputs.
* Provider-specific behaviour is acceptable behind a wrapper.

## 6.3 Adapt an API when

* An authoritative API exists but no suitable MCP server exists.
* The public ServiceFabric contract should differ from the provider API.
* Several provider calls must be normalized.
* Rate limiting, caching or evidence handling is needed.

## 6.4 Compose when

* Existing tools already provide the necessary primitives.
* A recurring sequence has one coherent outcome.
* No new external integration is required.
* Centralized recovery improves reliability.

---

# 7. External MCP ecosystem policy

ServiceFabric can use the official MCP Registry as a discovery source, but registry presence should not be interpreted as a security, quality or suitability endorsement. Every imported server must still pass ServiceFabric’s federation, security, schema, effect and evaluation gates. The official registry had become an active catalogue by July 2026 and included both established provider integrations and highly experimental servers.

Preferred federation order:

```text
1. Official provider-maintained server
2. Official protocol reference server
3. Well-maintained open-source provider adapter
4. Community server after full review
5. Native ServiceFabric adapter
```

The existence of an official server does not require ServiceFabric to expose its complete tool inventory. ServiceFabric should wrap only the capabilities it needs.

---

# 8. Platform and meta-tool portfolio

These are the highest-priority ServiceFabric-native tools.

## 8.1 Registry and discovery

| Priority | Tool                           | Purpose                                  |
| -------- | ------------------------------ | ---------------------------------------- |
| P0       | `registry.search_capabilities` | Find relevant ServiceFabric capabilities |
| P0       | `registry.describe_tool`       | Retrieve a full callable contract        |
| P0       | `registry.compare_tools`       | Compare similar tools                    |
| P0       | `registry.resolve_tool`        | Resolve version and deployment           |
| P1       | `registry.list_replacements`   | Find migration paths                     |
| P1       | `registry.report_gap`          | Record an unmet capability               |
| P2       | `registry.explain_selection`   | Explain ranking reason codes             |

## 8.2 Governance

| Priority | Tool                          | Purpose                        |
| -------- | ----------------------------- | ------------------------------ |
| P0       | `policy.evaluate`             | Produce policy decisions       |
| P0       | `policy.explain_decision`     | Explain a denial or obligation |
| P0       | `approval.create_preview`     | Construct an action preview    |
| P0       | `approval.verify`             | Verify approval binding        |
| P0       | `effects.verify`              | Verify an external effect      |
| P1       | `effects.reconcile`           | Resolve uncertain effect state |
| P1       | `authority.inspect_effective` | Inspect attenuated authority   |

Administrative writes should not be exposed to ordinary agents.

## 8.3 Operations

| Priority | Tool                              | Purpose                      |
| -------- | --------------------------------- | ---------------------------- |
| P0       | `operations.get_tool_health`      | Read ToolStatus              |
| P0       | `operations.get_provider_health`  | Read dependency status       |
| P0       | `operations.report_failure`       | Submit a structured failure  |
| P1       | `operations.explain_degradation`  | Explain reduced capability   |
| P1       | `operations.get_incident`         | Read an incident             |
| P2       | `operations.request_health_probe` | Request bounded verification |

## 8.4 Evaluation

| Priority | Tool                                 | Purpose                           |
| -------- | ------------------------------------ | --------------------------------- |
| P0       | `evaluations.run_suite`              | Execute a registered suite        |
| P0       | `evaluations.get_report`             | Read evaluation results           |
| P1       | `evaluations.compare_revisions`      | Compare baseline and candidate    |
| P1       | `evaluations.create_regression_case` | Convert failure into a case       |
| P2       | `quality.get_tool_vector`            | Retrieve multidimensional quality |
| P2       | `cost.get_objective_cost`            | Retrieve attributed cost          |

---

# 9. Universal primitive portfolio

## 9.1 Calculation

| Priority | Tool                         | Agentic backing         |
| -------- | ---------------------------- | ----------------------- |
| P0       | `math.calculate`             | Guarded deterministic   |
| P1       | `math.solve_equation`        | Deterministic           |
| P1       | `statistics.describe`        | Deterministic           |
| P1       | `statistics.test_hypothesis` | Deterministic           |
| P1       | `statistics.fit_regression`  | Deterministic           |
| P2       | `optimisation.solve`         | Guarded deterministic   |
| P2       | `simulation.run_monte_carlo` | Deterministic execution |

`math.calculate` should be implemented first because it provides exact arithmetic to every graph while establishing the simplest Tool Capsule reference implementation.

## 9.2 Time and dates

| Priority | Tool                               | Purpose                       |
| -------- | ---------------------------------- | ----------------------------- |
| P0       | `time.get_current`                 | Current time in a location    |
| P0       | `time.convert_timezone`            | Convert time zones            |
| P0       | `dates.calculate`                  | Date arithmetic               |
| P1       | `dates.get_holiday`                | Jurisdictional holiday lookup |
| P1       | `calendar.calculate_business_days` | Business-day calculations     |

## 9.3 Units and currencies

| Priority | Tool                        | Purpose                                 |
| -------- | --------------------------- | --------------------------------------- |
| P0       | `units.convert`             | Deterministic unit conversion           |
| P1       | `currency.convert`          | FX conversion with source and timestamp |
| P1       | `currency.normalize_amount` | Canonical monetary representation       |
| P1       | `currency.validate_code`    | ISO currency validation                 |

`currency.convert` is retrieval plus calculation; it must expose the rate source, rate timestamp and whether the rate is historical, indicative or executable.

## 9.4 HTTP and APIs

| Priority | Tool                       | Purpose                             |
| -------- | -------------------------- | ----------------------------------- |
| P0       | `http.request`             | Bounded allowlisted request         |
| P1       | `http.get_json`            | Retrieve validated JSON             |
| P1       | `http.download_resource`   | Download a bounded resource         |
| P1       | `api.describe_openapi`     | Read an OpenAPI contract            |
| P2       | `api.invoke_operation`     | Invoke an allowlisted API operation |
| P2       | `api.check_contract_drift` | Compare current and prior contracts |

A generic HTTP tool should be internal-only by default. External agents should normally call domain tools that impose provider, schema and evidence controls.

## 9.5 Structured data

| Priority | Tool                   | Purpose                               |
| -------- | ---------------------- | ------------------------------------- |
| P0       | `data.inspect_schema`  | Describe tables or records            |
| P0       | `data.select`          | Filter and project structured data    |
| P0       | `data.join`            | Join datasets                         |
| P0       | `data.aggregate`       | Group and summarize                   |
| P1       | `data.validate`        | Validate against a schema             |
| P1       | `data.transform`       | Apply declared transformations        |
| P1       | `data.profile_quality` | Missingness, uniqueness and anomalies |
| P2       | `data.reconcile`       | Compare two datasets                  |
| P2       | `data.build_lineage`   | Produce lineage evidence              |

These tools should use declarative operation specifications rather than unrestricted generated code where possible.

## 9.6 Files and artifacts

| Priority | Tool                   | Purpose                            |
| -------- | ---------------------- | ---------------------------------- |
| P0       | `files.read`           | Read authorized artifact           |
| P0       | `files.list`           | List authorized directory or store |
| P1       | `files.write`          | Write approved artifact            |
| P1       | `files.compare`        | Compare versions                   |
| P1       | `files.hash`           | Calculate integrity hash           |
| P1       | `files.convert`        | Convert supported formats          |
| P2       | `files.archive`        | Produce an archive                 |
| P2       | `files.search_content` | Search indexed file contents       |

Filesystem tools require explicit path and tenant restrictions.

## 9.7 Documents

| Priority | Tool                         | Purpose                                |
| -------- | ---------------------------- | -------------------------------------- |
| P0       | `documents.extract_text`     | Extract text and structure             |
| P1       | `documents.extract_tables`   | Extract tabular content                |
| P1       | `documents.extract_metadata` | Identify authors, dates and properties |
| P1       | `documents.chunk`            | Create traceable chunks                |
| P1       | `documents.compare_versions` | Compare document changes               |
| P2       | `documents.render`           | Render into a target format            |
| P2       | `documents.verify_reference` | Verify a location in a document        |

Document extraction should preserve page, section, table and source-location metadata.

## 9.8 Sandboxed code

| Priority | Tool                        | Purpose                     |
| -------- | --------------------------- | --------------------------- |
| P0       | `code.run_python`           | Execute bounded Python      |
| P1       | `code.run_typescript`       | Execute bounded TypeScript  |
| P1       | `code.run_command`          | Execute allowlisted command |
| P1       | `code.install_dependencies` | Build-time sandbox only     |
| P2       | `code.profile_execution`    | CPU and memory profile      |

Generic code tools are powerful but high-risk. They should be restricted to graphs whose objectives genuinely require computation unavailable through declarative tools.

---

# 10. Web and browser portfolio

## 10.1 Search and retrieval

| Priority | Tool                      | Purpose                            |
| -------- | ------------------------- | ---------------------------------- |
| P0       | `web.search_pages`        | Search public web pages            |
| P0       | `web.retrieve_page`       | Retrieve a known page              |
| P1       | `web.extract_content`     | Extract main content               |
| P1       | `web.retrieve_sitemap`    | Discover site structure            |
| P1       | `web.find_on_page`        | Locate text or structured elements |
| P2       | `web.compare_sources`     | Compare claims across pages        |
| P2       | `web.monitor_page_change` | Detect material changes            |

Separate:

```text
Search
    Finds candidate sources.

Retrieve
    Obtains a known source.

Extract
    Converts source into structured content.

Verify
    Tests a claim against the source.
```

## 10.2 Browser automation

| Priority | Tool                                 | Purpose                     |
| -------- | ------------------------------------ | --------------------------- |
| P1       | `browser.open_page`                  | Open a browser page         |
| P1       | `browser.inspect_accessibility_tree` | Read structured page state  |
| P1       | `browser.interact`                   | Execute bounded interaction |
| P1       | `browser.capture_screenshot`         | Capture visual evidence     |
| P2       | `browser.complete_workflow`          | Execute registered workflow |
| P2       | `browser.compare_visuals`            | Compare rendered results    |

Playwright’s official MCP server provides browser automation through structured accessibility snapshots and supports capability-based control over which browser tool groups are exposed. This makes it a strong federation candidate for ServiceFabric, provided browser state, profiles, credentials and writable interactions remain governed by a ServiceFabric wrapper.

## 10.3 Web-development diagnostics

| Priority | Tool                             | Purpose                            |
| -------- | -------------------------------- | ---------------------------------- |
| P1       | `web.inspect_dom`                | Inspect DOM structure              |
| P1       | `web.run_accessibility_audit`    | Evaluate accessibility rules       |
| P1       | `web.measure_performance`        | Capture performance indicators     |
| P1       | `web.inspect_network`            | Inspect browser requests           |
| P2       | `web.compare_visuals`            | Identify visual regressions        |
| P2       | `web.validate_responsive_layout` | Test viewport behavior             |
| P2       | `web.check_links`                | Verify internal and external links |
| P2       | `web.inspect_console`            | Retrieve runtime browser errors    |

## 10.4 Web-development composites

```text
web.audit_page
    accessibility
    performance
    broken links
    console errors
    metadata
    screenshots

web.validate_release
    deploy preview
    run frontend tests
    capture screenshots
    compare baseline
    accessibility audit
    produce report
```

---

# 11. Software-engineering portfolio

## 11.1 Repository discovery and reading

| Priority | Tool                              | Purpose                          |
| -------- | --------------------------------- | -------------------------------- |
| P0       | `software.search_repository`      | Semantic and lexical code search |
| P0       | `software.read_file`              | Read repository file             |
| P1       | `software.inspect_symbol`         | Find definition and references   |
| P1       | `software.inspect_commit`         | Read commit changes              |
| P1       | `software.inspect_dependency`     | Inspect dependency metadata      |
| P2       | `software.build_dependency_graph` | Build code dependency graph      |

## 11.2 Build and verification

| Priority | Tool                           | Purpose                    |
| -------- | ------------------------------ | -------------------------- |
| P0       | `software.run_tests`           | Execute tests              |
| P0       | `software.compile`             | Compile or build           |
| P1       | `software.run_linter`          | Lint                       |
| P1       | `software.run_typecheck`       | Type validation            |
| P1       | `software.run_static_analysis` | Static analysis            |
| P1       | `software.scan_dependencies`   | Dependency vulnerabilities |
| P2       | `software.measure_coverage`    | Test coverage              |
| P2       | `software.run_benchmark`       | Performance benchmark      |

## 11.3 Repository actions

| Priority   | Tool                           | Purpose                |
| ---------- | ------------------------------ | ---------------------- |
| P2         | `software.prepare_patch`       | Produce proposed patch |
| P4         | `software.apply_patch`         | Write change to branch |
| P4         | `software.create_branch`       | Create branch          |
| P4         | `software.create_pull_request` | Open pull request      |
| P4         | `software.update_issue`        | Update issue           |
| Restricted | `software.merge_pull_request`  | Merge after approval   |

GitHub maintains an official MCP server that can read repositories and code, manage issues and pull requests, analyze code and automate workflows. ServiceFabric should federate a limited subset or use it as the provider adapter behind its own stable tools, rather than exposing the entire GitHub inventory to every coding graph.

## 11.4 Software composites

### `software.validate_change`

```text
Input:
    Proposed patch or branch.

Internal sequence:
    inspect changed files
    compile
    type-check
    lint
    run affected tests
    security scan
    summarize evidence

Output:
    validation report
    failed checks
    affected components
    evidence references
```

### `software.investigate_failure`

```text
Input:
    Repository, commit and failed execution.

Internal sequence:
    reproduce
    retrieve logs
    inspect related code
    identify hypotheses
    run bounded tests
    rank likely causes

Output:
    reproducible failure
    evidence
    root-cause candidates
    recommended next action
```

### `software.prepare_pull_request`

```text
Input:
    Approved proposed change.

Internal sequence:
    apply patch to feature branch
    validate change
    generate PR description
    create pull request

Effect:
    Reversible repository write and external collaboration action.
```

---

# 12. Database and data-platform portfolio

## 12.1 Database primitives

| Priority | Tool                         | Purpose                        |
| -------- | ---------------------------- | ------------------------------ |
| P0       | `database.inspect_schema`    | Read database structure        |
| P0       | `database.query_readonly`    | Execute constrained read query |
| P1       | `database.explain_query`     | Query execution plan           |
| P1       | `database.profile_table`     | Data quality and distributions |
| P2       | `database.prepare_migration` | Generate migration proposal    |
| P4       | `database.apply_migration`   | Apply approved migration       |
| P4       | `database.execute_write`     | Approved bounded write         |

Google’s official MCP Toolbox for Databases is designed to connect agents and applications to enterprise databases. It is a useful reference or federation candidate, but ServiceFabric should still impose its own schema, query, tenant, read/write and result-size controls.

Supabase also provides an MCP server that can query projects and perform administrative database operations. Because its capability set can include schema changes, Edge Function deployment and other persistent effects, ServiceFabric should separate read-only database capabilities from administrative actions and apply its own approval layer.

## 12.2 Data-engineering composites

```text
data.build_dataset
    discover sources
    retrieve
    normalize
    join
    validate
    create lineage

data.reconcile_sources
    align keys
    compare values
    classify differences
    calculate materiality
    produce exception report

data.prepare_pipeline
    inspect source
    infer schema
    propose transformations
    generate validation rules
    produce deployment artifact
```

---

# 13. Research portfolio

## 13.1 Scholarly discovery

| Priority | Tool                          | Purpose                                |
| -------- | ----------------------------- | -------------------------------------- |
| P1       | `research.search_papers`      | Search normalized scholarly indexes    |
| P1       | `research.search_preprints`   | Search preprint sources                |
| P1       | `research.resolve_identifier` | Resolve DOI, arXiv or other identifier |
| P1       | `research.retrieve_metadata`  | Retrieve authoritative metadata        |
| P2       | `research.find_related_work`  | Related-paper discovery                |
| P2       | `research.search_citations`   | Citation relationship search           |

The official arXiv API supports programmatic access to its e-print records and returns structured metadata. Its own guidance includes API terms and responsible-use requirements, so an arXiv adapter should include rate limiting, attribution, caching and provider-specific maintenance.

## 13.2 Retrieval and document understanding

| Priority | Tool                             | Purpose                                  |
| -------- | -------------------------------- | ---------------------------------------- |
| P1       | `research.retrieve_paper`        | Retrieve a known paper                   |
| P1       | `research.extract_structure`     | Sections, tables, figures and references |
| P1       | `research.extract_methods`       | Extract method details                   |
| P1       | `research.extract_findings`      | Extract reported findings                |
| P2       | `research.extract_dataset_usage` | Identify datasets                        |
| P2       | `research.extract_limitations`   | Extract limitations                      |

## 13.3 Verification

| Priority | Tool                               | Purpose                           |
| -------- | ---------------------------------- | --------------------------------- |
| P1       | `research.validate_citation`       | Validate bibliographic identity   |
| P1       | `research.verify_quotation`        | Verify text against source        |
| P1       | `research.verify_claim_support`    | Assess source support             |
| P2       | `research.compare_metadata`        | Resolve metadata conflict         |
| P2       | `research.check_retraction_status` | Check status where sources permit |
| P2       | `research.assess_source_quality`   | Structured quality indicators     |

## 13.4 Research composites

### `research.build_evidence_set`

```text
search scholarly records
retrieve metadata
deduplicate
validate identifiers
retrieve selected papers
extract relevant findings
attach provenance
group supporting and conflicting evidence
```

### `research.review_literature`

```text
Input:
    Bounded research question and review criteria.

Output:
    Search strategy
    Included and excluded records
    Evidence table
    Themes
    Conflicts
    Limitations
    Research gaps
```

### `research.investigate_question`

This is the higher-level agent-backed service.

It may plan searches and iterate, but must declare:

* Maximum searches
* Maximum documents
* Inclusion criteria
* Evidence threshold
* Stopping condition
* Whether synthesis is descriptive or evaluative

---

# 14. Learning portfolio

## 14.1 Knowledge modeling

| Priority | Tool                              | Purpose                              |
| -------- | --------------------------------- | ------------------------------------ |
| P2       | `learning.map_concepts`           | Build concept graph                  |
| P2       | `learning.identify_prerequisites` | Identify dependencies                |
| P2       | `learning.assess_knowledge`       | Structured diagnostic                |
| P2       | `learning.retrieve_materials`     | Retrieve approved learning resources |

## 14.2 Practice and assessment

| Priority | Tool                              | Purpose                     |
| -------- | --------------------------------- | --------------------------- |
| P2       | `learning.generate_exercises`     | Generate bounded practice   |
| P2       | `learning.grade_response`         | Grade against rubric        |
| P2       | `learning.explain_error`          | Explain misconception       |
| P2       | `learning.generate_flashcards`    | Create traceable flashcards |
| P3       | `learning.build_practice_session` | Compose learning sequence   |
| P3       | `learning.update_learning_plan`   | Adapt plan from evidence    |

## 14.3 Learning safeguards

Learning tools should distinguish:

```text
Source-grounded fact
Model-generated explanation
Practice question
Grading judgment
```

A generated exercise should not be treated as an authoritative source.

---

# 15. Financial-analysis portfolio

ServiceFabric’s finance portfolio should be split into:

```text
Reference and market data
Company and filing data
Portfolio data
Calculation and modelling
Validation and reconciliation
Research synthesis
Transaction preparation
Transaction commitment
```

---

# 16. Financial data primitives

## 16.1 Market and reference data

| Priority | Tool                                  | Purpose                  |
| -------- | ------------------------------------- | ------------------------ |
| P1       | `finance.retrieve_market_price`       | Timestamped market price |
| P1       | `finance.retrieve_price_history`      | Historical prices        |
| P1       | `finance.retrieve_fx_rate`            | FX rate                  |
| P1       | `finance.retrieve_yield_curve`        | Yield curve              |
| P1       | `finance.retrieve_instrument`         | Security master data     |
| P2       | `finance.retrieve_corporate_actions`  | Corporate-action records |
| P2       | `finance.retrieve_index_constituents` | Index membership         |

Every returned financial observation should include:

* Source
* Observation time
* Retrieval time
* Currency
* Adjustment status
* Data frequency
* Whether values are revised, indicative or final

## 16.2 Macroeconomic data

| Priority | Tool                         | Purpose                     |
| -------- | ---------------------------- | --------------------------- |
| P1       | `economics.search_series`    | Discover economic series    |
| P1       | `economics.retrieve_series`  | Retrieve observations       |
| P2       | `economics.retrieve_vintage` | Retrieve historical vintage |
| P2       | `economics.align_series`     | Align frequencies and dates |

FRED provides official APIs for discovering and retrieving economic series, releases and observations, while ALFRED supports historical vintage analysis. This makes FRED a strong authoritative provider adapter for macroeconomic tools.

## 16.3 Filings and corporate disclosure

| Priority | Tool                             | Purpose                      |
| -------- | -------------------------------- | ---------------------------- |
| P1       | `finance.search_filings`         | Discover filings             |
| P1       | `finance.retrieve_filing`        | Retrieve filing              |
| P1       | `finance.retrieve_company_facts` | Structured reported facts    |
| P1       | `finance.extract_statements`     | Extract financial statements |
| P2       | `finance.extract_filing_events`  | Identify material events     |
| P2       | `finance.compare_filings`        | Compare reporting periods    |

The SEC provides public EDGAR APIs for company submissions and extracted XBRL facts in JSON form. These should be wrapped with identifier normalization, fair-access controls, filing-version metadata and provenance.

---

# 17. WRDS and quantitative-research portfolio

Given ServiceFabric’s intended finance and research use, WRDS should become a dedicated provider domain.

## 17.1 WRDS primitives

| Priority | Tool                       | Purpose                       |
| -------- | -------------------------- | ----------------------------- |
| P1       | `wrds.list_libraries`      | List licensed databases       |
| P1       | `wrds.list_tables`         | List tables                   |
| P1       | `wrds.describe_table`      | Inspect fields and keys       |
| P1       | `wrds.query_readonly`      | Execute controlled query      |
| P1       | `wrds.retrieve_crsp`       | Retrieve normalized CRSP data |
| P1       | `wrds.retrieve_compustat`  | Retrieve Compustat data       |
| P2       | `wrds.retrieve_ravenpack`  | Retrieve RavenPack data       |
| P2       | `wrds.retrieve_accern`     | Retrieve Accern data          |
| P2       | `wrds.link_crsp_compustat` | Apply linking logic           |
| P2       | `wrds.validate_extract`    | Validate returned dataset     |

WRDS officially supports Python as well as ODBC and JDBC access, and its Python tooling can enumerate libraries and datasets and retrieve structured data. This supports a native ServiceFabric adapter with licence-aware access, query limits, dataset-specific contracts and reproducibility metadata.

## 17.2 WRDS tool design

Do not expose only:

```text
wrds.run_sql
```

Instead provide both:

```text
wrds.query_readonly
    Flexible expert capability.

wrds.retrieve_crsp
wrds.retrieve_compustat
wrds.link_crsp_compustat
    Safer domain capabilities.
```

`wrds.query_readonly` should enforce:

* Read-only SQL
* Table allowlists
* Row limits
* Cost or complexity limits
* Query timeout
* Licence constraints
* No credential disclosure
* Reproducible query record

## 17.3 CRSP-specific tools

```text
crsp.retrieve_security_master
crsp.retrieve_daily_stock
crsp.retrieve_monthly_stock
crsp.retrieve_delisting_returns
crsp.retrieve_distributions
crsp.retrieve_market_indexes
crsp.build_total_return_series
crsp.validate_security_history
```

## 17.4 Compustat-specific tools

```text
compustat.retrieve_company
compustat.retrieve_fundamentals
compustat.retrieve_segments
compustat.retrieve_pension_data
compustat.normalize_statements
```

## 17.5 Quantitative research composites

```text
finance.build_equity_research_panel
    retrieve CRSP
    retrieve Compustat
    link identifiers
    align dates
    calculate returns
    validate survivorship and delisting treatment

finance.build_event_study_dataset
    retrieve events
    identify securities
    retrieve estimation and event windows
    calculate expected returns
    calculate abnormal returns
    produce diagnostics

finance.build_news_signal_dataset
    retrieve news analytics
    link entities and securities
    align timestamps
    apply lag policy
    join market outcomes
    detect leakage
```

---

# 18. Financial calculation portfolio

| Priority | Tool                               | Purpose                     |
| -------- | ---------------------------------- | --------------------------- |
| P1       | `finance.calculate_returns`        | Returns and total returns   |
| P1       | `finance.calculate_ratios`         | Financial ratios            |
| P1       | `finance.calculate_present_value`  | Discounted value            |
| P1       | `finance.calculate_duration`       | Duration and convexity      |
| P1       | `finance.price_option`             | Declared option model       |
| P1       | `finance.calculate_portfolio_risk` | Risk measures               |
| P2       | `finance.calculate_var`            | VaR with explicit method    |
| P2       | `finance.run_stress_scenario`      | Scenario impact             |
| P2       | `finance.attribute_performance`    | Performance attribution     |
| P2       | `finance.optimise_portfolio`       | Constrained optimization    |
| P2       | `finance.model_credit_risk`        | Credit-risk model execution |

Each calculation tool should return:

* Method
* Inputs
* Assumptions
* Units
* Output
* Diagnostics
* Reproducibility information

---

# 19. Financial validation and controls

| Priority | Tool                                   | Purpose                              |
| -------- | -------------------------------------- | ------------------------------------ |
| P1       | `finance.validate_market_data`         | Detect stale or invalid data         |
| P1       | `finance.reconcile_positions`          | Compare position sources             |
| P1       | `finance.reconcile_cash`               | Compare cash records                 |
| P1       | `finance.validate_transaction`         | Validate proposed transaction        |
| P2       | `finance.detect_outliers`              | Identify unusual observations        |
| P2       | `finance.check_limit`                  | Check portfolio or transaction limit |
| P2       | `finance.explain_reconciliation_break` | Classify differences                 |

These tools should be deterministic wherever possible.

---

# 20. Financial composites

## 20.1 `finance.build_company_dataset`

```text
resolve company
retrieve filings
retrieve structured company facts
retrieve market data
normalize financial statements
calculate ratios
validate dates and currencies
produce evidence-linked dataset
```

## 20.2 `finance.analyse_company`

```text
Input:
    Company, period and analysis scope.

Internal sequence:
    build company dataset
    analyze profitability
    analyze capital structure
    analyze cash flow
    analyze valuation
    identify material changes
    retrieve supporting filings
    produce evidence-linked report
```

## 20.3 `finance.analyse_portfolio`

```text
retrieve positions
retrieve prices and FX
validate market data
calculate exposures
calculate risk
run stress scenarios
identify limits
produce report
```

## 20.4 `finance.investigate_reconciliation_break`

```text
retrieve both ledgers
normalize identifiers
compare records
classify timing, amount and reference differences
retrieve transaction evidence
rank causes
produce exception recommendations
```

---

# 21. Financial action tools

These should be implemented only after read, analysis, preparation, approval and reconciliation foundations are mature.

| Priority   | Tool                            | Effect                           |
| ---------- | ------------------------------- | -------------------------------- |
| P3         | `finance.prepare_transaction`   | No commitment                    |
| P3         | `finance.prepare_payment`       | No commitment                    |
| P4         | `finance.submit_transaction`    | Financial commitment             |
| P4         | `finance.submit_payment`        | Financial commitment             |
| P4         | `finance.cancel_transaction`    | External effect                  |
| P4         | `finance.reconcile_transaction` | Verification                     |
| Restricted | `finance.modify_beneficiary`    | Administrative financial control |

Action and validation tools must be separate.

---

# 22. Productivity portfolio

## 22.1 Communication

| Priority | Tool                            | Purpose                    |
| -------- | ------------------------------- | -------------------------- |
| P1       | `communication.search_messages` | Search authorized messages |
| P1       | `communication.read_message`    | Read message               |
| P2       | `communication.prepare_email`   | Produce reviewable email   |
| P2       | `communication.prepare_reply`   | Produce reply              |
| P4       | `communication.send_email`      | Send approved email        |
| P4       | `communication.forward_message` | Forward approved message   |
| P4       | `communication.apply_label`     | Modify mailbox state       |

## 22.2 Calendar

| Priority | Tool                          | Purpose                |
| -------- | ----------------------------- | ---------------------- |
| P1       | `calendar.search_events`      | Search events          |
| P1       | `calendar.check_availability` | Determine availability |
| P2       | `calendar.prepare_event`      | Create event preview   |
| P4       | `calendar.create_event`       | Create event           |
| P4       | `calendar.update_event`       | Modify event           |
| P4       | `calendar.respond_invitation` | Respond to invitation  |

## 22.3 Documents and collaboration

| Priority | Tool                          | Purpose                     |
| -------- | ----------------------------- | --------------------------- |
| P1       | `workspace.search_documents`  | Search enterprise documents |
| P1       | `workspace.read_document`     | Read authorized document    |
| P2       | `workspace.create_document`   | Create artifact             |
| P2       | `workspace.update_document`   | Modify artifact             |
| P2       | `workspace.comment_document`  | Add comment                 |
| P2       | `workspace.compare_documents` | Compare versions            |

Microsoft introduced several MCP-oriented enterprise and productivity services during 2026, including an enterprise Microsoft Graph server, Microsoft Learn and release-information servers, and Power BI MCP servers in preview. These are potential federation targets, but preview status, tenant permissions and tool-level effects must be preserved in the ServiceFabric wrapper.

---

# 23. Project-management portfolio

## 23.1 Read and discovery

| Priority | Tool                       | Purpose                    |
| -------- | -------------------------- | -------------------------- |
| P1       | `project.search_projects`  | Search authorized projects |
| P1       | `project.get_project`      | Retrieve project state     |
| P1       | `project.search_tasks`     | Search tasks               |
| P1       | `project.get_task`         | Retrieve task              |
| P1       | `project.get_milestones`   | Retrieve milestones        |
| P1       | `project.get_dependencies` | Retrieve dependencies      |
| P1       | `project.get_risks`        | Retrieve risk register     |

## 23.2 Analysis

| Priority | Tool                                  | Purpose             |
| -------- | ------------------------------------- | ------------------- |
| P2       | `project.calculate_schedule_variance` | Schedule variance   |
| P2       | `project.calculate_cost_variance`     | Cost variance       |
| P2       | `project.assess_dependency_risk`      | Dependency risk     |
| P2       | `project.detect_blockers`             | Identify blockers   |
| P2       | `project.forecast_completion`         | Forecast completion |
| P2       | `project.assess_capacity`             | Capacity assessment |

## 23.3 Actions

| Priority | Tool                       | Purpose             |
| -------- | -------------------------- | ------------------- |
| P2       | `project.prepare_task`     | Action preview      |
| P4       | `project.create_task`      | Create task         |
| P4       | `project.update_task`      | Update task         |
| P4       | `project.create_risk`      | Add risk            |
| P4       | `project.update_milestone` | Modify milestone    |
| P4       | `project.assign_resource`  | Resource assignment |

## 23.4 Composites

### `project.prepare_status_report`

```text
retrieve milestones
retrieve tasks
retrieve risks and issues
calculate variances
identify changes since last report
draft evidence-linked report
```

### `project.assess_delivery_risk`

```text
analyse schedule
analyse dependencies
analyse unresolved issues
analyse capacity
compare historical delivery
rank risks
recommend bounded interventions
```

### `project.plan_work`

```text
decompose objective
identify dependencies
estimate effort ranges
check capacity
produce proposed tasks
require approval before creation
```

Atlassian provides an official Forge MCP server for authoritative platform and developer knowledge. ServiceFabric may federate it for development support, while project actions in Jira or related systems should use separately governed provider adapters or reviewed MCP capabilities.

---

# 24. Organisational-effectiveness portfolio

## 24.1 Data retrieval

| Priority | Tool                                      | Purpose                |
| -------- | ----------------------------------------- | ---------------------- |
| P2       | `organisation.retrieve_unit_metrics`      | Unit-level metrics     |
| P2       | `organisation.retrieve_workforce_metrics` | Staffing and workload  |
| P2       | `organisation.retrieve_process_data`      | Process observations   |
| P2       | `organisation.retrieve_budget_metrics`    | Budget and expenditure |
| P2       | `organisation.retrieve_service_metrics`   | Service delivery       |

## 24.2 Analytical primitives

| Priority | Tool                                   | Purpose                      |
| -------- | -------------------------------------- | ---------------------------- |
| P2       | `organisation.compare_units`           | Comparable unit benchmarking |
| P2       | `organisation.analyse_workloads`       | Workload distribution        |
| P2       | `organisation.map_process`             | Process representation       |
| P2       | `organisation.calculate_efficiency`    | Input-output efficiency      |
| P2       | `organisation.detect_bottlenecks`      | Process bottlenecks          |
| P2       | `organisation.analyse_span_of_control` | Management structure         |
| P2       | `organisation.analyse_network`         | Collaboration relationships  |
| P2       | `organisation.model_staffing`          | Staffing scenarios           |

## 24.3 Organisational composites

### `organisation.benchmark_units`

```text
retrieve unit metrics
define comparison population
normalize for size and mandate
calculate similarity
calculate benchmarks
identify outliers
produce limitations and evidence
```

### `organisation.assess_operating_model`

```text
map functions
map decision rights
map processes
map systems
analyse workload
analyse fragmentation
identify gaps and overlaps
produce scenario options
```

### `organisation.diagnose_performance`

```text
Input:
    Bounded organizational performance question.

Internal sequence:
    retrieve metrics
    validate comparability
    identify material changes
    inspect process and workload factors
    test alternative explanations
    produce evidence-ranked findings

Output:
    findings
    confidence
    limitations
    management options
```

---

# 25. Management portfolio

Management tools should support decision processes without pretending that judgment has been reduced to automation.

## 25.1 Decision support

| Priority | Tool                               | Purpose                      |
| -------- | ---------------------------------- | ---------------------------- |
| P2       | `management.structure_decision`    | Define decision and criteria |
| P2       | `management.compare_options`       | Multi-criteria comparison    |
| P2       | `management.assess_risk`           | Structured risk assessment   |
| P2       | `management.run_scenario`          | Scenario comparison          |
| P2       | `management.build_decision_record` | Document rationale           |
| P2       | `management.track_decision`        | Monitor implementation       |

## 25.2 Meeting and communication support

| Priority | Tool                               | Purpose                    |
| -------- | ---------------------------------- | -------------------------- |
| P2       | `management.prepare_brief`         | Executive brief            |
| P2       | `management.prepare_meeting`       | Agenda and evidence        |
| P2       | `management.extract_actions`       | Extract proposed actions   |
| P3       | `management.prepare_decision_pack` | Composite decision package |

## 25.3 Decision authority

A management analysis tool may:

* Structure options
* Calculate implications
* Retrieve evidence
* Identify uncertainty
* Record assumptions

It should not claim organizational authority to select or execute an option unless a separate approved action workflow exists.

---

# 26. Cloud and infrastructure portfolio

## 26.1 Read and diagnose

| Priority | Tool                                  | Purpose                       |
| -------- | ------------------------------------- | ----------------------------- |
| P1       | `infrastructure.search_documentation` | Search provider documentation |
| P1       | `infrastructure.get_resource`         | Read resource state           |
| P1       | `infrastructure.query_logs`           | Query logs                    |
| P1       | `infrastructure.query_metrics`        | Query metrics                 |
| P2       | `infrastructure.inspect_deployment`   | Inspect deployment            |
| P2       | `infrastructure.diagnose_incident`    | Bounded diagnosis             |

## 26.2 Actions

| Priority   | Tool                             | Purpose                 |
| ---------- | -------------------------------- | ----------------------- |
| P3         | `infrastructure.prepare_change`  | Change proposal         |
| P4         | `infrastructure.deploy`          | Deploy artifact         |
| P4         | `infrastructure.scale_resource`  | Scale resource          |
| P4         | `infrastructure.rollback`        | Roll back deployment    |
| Restricted | `infrastructure.modify_identity` | Security administration |

AWS provides a managed MCP server with documentation retrieval, authenticated API access and sandboxed script execution under IAM controls. This makes it a useful federation reference, but ServiceFabric should still restrict specific AWS operations, resource selectors and effect classes through its own governance layer.

---

# 27. The first native ServiceFabric reference portfolio

The first implementation portfolio should contain twelve tools.

## 27.1 Platform tools

```text
1. registry.search_capabilities
2. registry.describe_tool
3. operations.get_tool_health
4. evaluations.run_suite
```

## 27.2 Universal primitives

```text
5. math.calculate
6. http.get_json
7. data.inspect_schema
8. data.transform
9. documents.extract_text
10. code.run_python
```

## 27.3 Representative advanced tools

```text
11. research.search_papers
12. project.create_task
```

These twelve provide deliberately different implementation profiles:

| Tool                           | Profile                           |
| ------------------------------ | --------------------------------- |
| `registry.search_capabilities` | Meta-tool                         |
| `registry.describe_tool`       | Registry read                     |
| `operations.get_tool_health`   | Operational read                  |
| `evaluations.run_suite`        | Long-running controlled operation |
| `math.calculate`               | Deterministic primitive           |
| `http.get_json`                | Guarded external retrieval        |
| `data.inspect_schema`          | Structured-data primitive         |
| `data.transform`               | Deterministic transformation      |
| `documents.extract_text`       | Artifact processing               |
| `code.run_python`              | Sandboxed execution               |
| `research.search_papers`       | Agent-assisted retrieval          |
| `project.create_task`          | Governed reversible write         |

Together, they test almost every major Tool Capsule concern.

---

# 28. Recommended build sequence

## Wave 0 — Control plane

Build:

```text
ToolDefinition schema
Tool Capsule runtime
Registry
Policy enforcement
Telemetry
Evaluation runner
MCP gateway
```

No broad domain expansion should precede this foundation.

## Wave 1 — Deterministic primitives

Build:

```text
math.calculate
dates.calculate
units.convert
data.inspect_schema
data.select
data.join
data.aggregate
data.validate
files.read
documents.extract_text
```

Objective:

* Prove schemas
* Prove Tool Capsule runtime
* Prove maintenance hooks
* Prove telemetry
* Prove MCP projection
* Prove evaluation

## Wave 2 — External retrieval

Build:

```text
http.get_json
web.search_pages
web.retrieve_page
research.search_papers
economics.retrieve_series
finance.retrieve_filing
```

Objective:

* Provider routing
* Caching
* Provenance
* Freshness
* Rate limiting
* Partial results
* Contract drift

## Wave 3 — Software and web engineering

Federate or adapt:

```text
browser.*
software.search_repository
software.run_tests
software.compile
software.run_static_analysis
```

Objective:

* Browser state
* Sandbox execution
* Repository access
* Artifact handling
* Provider MCP federation

## Wave 4 — Finance and WRDS

Build:

```text
wrds.*
crsp.*
compustat.*
finance.calculate_returns
finance.calculate_portfolio_risk
finance.build_equity_research_panel
finance.build_company_dataset
```

Objective:

* Licensed data access
* Identifier linkage
* Temporal correctness
* Financial reproducibility
* Data lineage

## Wave 5 — Productivity and project actions

Build:

```text
communication.prepare_email
calendar.check_availability
project.search_tasks
project.prepare_task
project.create_task
```

Objective:

* Delegated user identity
* Approval
* Idempotency
* Effect verification
* Reconciliation

## Wave 6 — Composite agents

Build only after primitives are mature:

```text
research.build_evidence_set
software.investigate_failure
finance.analyse_company
finance.analyse_portfolio
project.assess_delivery_risk
organisation.benchmark_units
```

---

# 29. Recommended immediate implementation order

The next engineering backlog should be:

```text
1. math.calculate
2. registry.search_capabilities
3. registry.describe_tool
4. operations.get_tool_health
5. data.inspect_schema
6. data.transform
7. documents.extract_text
8. http.get_json
9. research.search_papers
10. code.run_python
11. software.run_tests
12. project.create_task
```

Rationale:

```text
math.calculate
    Simplest reference capsule.

registry tools
    Required before portfolio growth.

health tool
    Proves maintenance integration.

data and document tools
    Provide reusable inputs to most domains.

HTTP and research
    Prove external-provider maintenance.

Python and tests
    Prove sandboxed execution.

task creation
    Proves approval, idempotency and effect verification.
```

---

# 30. Native versus federated recommendations

| Capability           | Recommendation                                          |
| -------------------- | ------------------------------------------------------- |
| Calculator           | Native                                                  |
| Data transformation  | Native                                                  |
| Registry             | Native                                                  |
| Governance           | Native                                                  |
| Evaluation           | Native                                                  |
| Web search           | Native wrapper over provider(s)                         |
| arXiv                | Native provider adapter                                 |
| SEC filings          | Native provider adapter                                 |
| FRED                 | Native provider adapter                                 |
| WRDS                 | Native licensed adapter                                 |
| GitHub               | ServiceFabric wrapper over official MCP/API             |
| Browser automation   | Wrapper over Playwright MCP/runtime                     |
| Database access      | Native contract over provider toolbox                   |
| AWS                  | Limited wrapper over official MCP/API                   |
| Microsoft 365        | Selective federation by domain                          |
| Supabase             | Selective federation, separate reads and administration |
| Jira/project systems | Native ServiceFabric contract over provider connector   |

---

# 31. Federation acceptance score

Every external MCP server should be scored before adoption.

```typescript
export interface FederationAssessment {
  providerAuthority: number;
  maintenanceMaturity: number;
  schemaQuality: number;
  authenticationQuality: number;
  permissionGranularity: number;
  outputVerifiability: number;
  operationalObservability: number;
  protocolCompatibility: number;

  effectRisk: number;
  dataRisk: number;
  contractDriftRisk: number;
  toolCatalogueComplexity: number;
  providerLockIn: number;
}
```

Blocking conditions:

```text
Unknown server identity
No enforceable authentication
Undeclared side effects
Secrets required in model context
No output validation possible
No tenant isolation
Unbounded code execution
Token passthrough
Tool descriptions containing unsafe instructions
No viable maintenance ownership
```

---

# 32. Tool families and context exposure

ServiceFabric should group tools into context packs.

## Core pack

```text
registry.search_capabilities
registry.describe_tool
math.calculate
dates.calculate
units.convert
```

## Research pack

```text
web.search_pages
web.retrieve_page
research.search_papers
research.retrieve_paper
research.validate_citation
documents.extract_text
```

## Software pack

```text
software.search_repository
software.read_file
software.run_tests
software.compile
software.run_static_analysis
software.prepare_patch
```

## Finance pack

```text
finance.retrieve_market_data
finance.retrieve_filing
finance.calculate_ratios
finance.calculate_portfolio_risk
economics.retrieve_series
```

## Project pack

```text
project.search_tasks
project.get_project
project.assess_delivery_risk
project.prepare_task
project.create_task
```

A graph should receive only the relevant packs and then progressively retrieve full contracts.

---

# 33. Tool granularity rules

Create a distinct tool when operations differ materially in:

* Objective
* Required inputs
* Output meaning
* Authorization
* Side effects
* Approval
* Reliability
* Recovery
* Evaluation

Do not create a distinct public tool merely because:

* A different provider is used.
* A different endpoint is called.
* The implementation language differs.
* A different database table is accessed.
* The same operation has optional filters.
* One model is replaced by another.

---

# 34. Composite-tool qualification

A recurring sequence becomes a composite when:

```text
sequence recurrence ≥ defined threshold
AND one coherent objective exists
AND intermediate outputs are usually not consumed independently
AND combined effects can be governed
AND composite evaluation outperforms dynamic composition
```

Evidence should include:

* Frequency
* Successful sequence rate
* Average calls saved
* Reduced failure rate
* Reduced tool-selection errors
* Reduced context
* Reduced cost
* Improved evidence

---

# 35. Agent-backed service qualification

A domain capability should become agent-backed only when:

```text
Deterministic implementation is insufficient
AND bounded planning is intrinsic
AND intermediate tool use is valuable
AND completion can be verified
AND budgets can be enforced
AND evidence can be produced
```

Examples appropriate for agentic backing:

* Literature investigation
* Software failure diagnosis
* Financial anomaly investigation
* Project delivery-risk analysis
* Organisational operating-model diagnosis

Examples normally inappropriate:

* Calculator
* Date conversion
* Database schema validation
* FX multiplication
* Approval verification
* Effect verification
* Access control

---

# 36. Portfolio risk tiers

## Tier A — Pure and read-only

Examples:

```text
math.calculate
data.inspect_schema
research.search_papers
finance.retrieve_filing
```

Default:

* Automatic execution
* No human approval
* Standard audit
* Provider and data controls

## Tier B — Sandboxed or persistent internal artifact

Examples:

```text
code.run_python
files.write
workspace.create_document
software.prepare_patch
```

Default:

* Restricted targets
* Sandbox or reversible storage
* Policy-based approval

## Tier C — Reversible external action

Examples:

```text
project.create_task
calendar.create_event
software.create_pull_request
```

Default:

* Action preview
* Approval where policy requires
* Idempotency
* Effect verification

## Tier D — External communication or administrative control

Examples:

```text
communication.send_email
software.merge_pull_request
database.apply_migration
```

Default:

* Explicit approval
* Strong target validation
* Complete audit
* Rollback or reconciliation

## Tier E — Financial or irreversible

Examples:

```text
finance.submit_payment
finance.submit_transaction
files.delete_irreversibly
security.modify_access
```

Default:

* Segregated authority
* Dual approval
* Exact action binding
* Idempotency
* Reconciliation
* Independent verification

---

# 37. Domain coverage matrix

| Capability     |    Web | Software | Research |  Finance | Learning | Project | Productivity | Organisation |
| -------------- | -----: | -------: | -------: | -------: | -------: | ------: | -----------: | -----------: |
| Search         |   High |     High |     High |     High |     High |  Medium |         High |       Medium |
| Retrieval      |   High |     High |     High |     High |     High |    High |         High |         High |
| Calculation    | Medium |   Medium |   Medium |     High |   Medium |    High |       Medium |         High |
| Transformation |   High |     High |     High |     High |   Medium |  Medium |         High |         High |
| Verification   |   High |     High |     High | Critical |     High |    High |         High |         High |
| Action         | Medium |     High |      Low | Critical |      Low |    High |         High |       Medium |
| Evidence       |   High |     High | Critical | Critical |     High |    High |       Medium |     Critical |
| Simulation     | Medium |   Medium |   Medium |     High |   Medium |    High |          Low |         High |

This matrix supports the decision to prioritize universal retrieval, calculation, transformation and verification primitives before building broad domain agents.

---

# 38. Portfolio health metrics

```text
registered_tools_total
active_tools_total
deprecated_tools_total
quarantined_tools_total

capabilities_covered_total
capability_gaps_total

tools_by_domain
tools_by_effect_class
tools_by_agentic_level
tools_by_provider

tool_reuse_across_graphs
average_tools_exposed_per_graph
tool_selection_confusion_rate

unused_tools_total
duplicate_capabilities_total
provider_specific_public_tools_total

composite_tool_adoption
agent_backed_tool_cost
effectful_tool_incident_rate
```

## 38.1 Portfolio efficiency

```text
objectives completed
────────────────────
active public tools
```

A growing tool count without growing objective completion indicates portfolio fragmentation.

---

# 39. Portfolio review process

Quarterly portfolio review should identify:

* Unused tools
* Duplicated capabilities
* Confused tool pairs
* High-maintenance tools
* Provider-specific public tools
* Missing verification tools
* Action tools lacking preparation tools
* Tools lacking evidence
* Recurring compositions
* Candidate composites
* Candidate retirements
* Tools with excessive agentic backing

The review outputs:

```text
Build requests
Evolution requests
Merge proposals
Split proposals
Composite proposals
Deprecation notices
Retirement proposals
```

---

# 40. Portfolio invariants

```text
SF-P001  Platform and governance tools precede broad domain expansion.
SF-P002  Deterministic primitives precede equivalent agentic tools.
SF-P003  Read capabilities precede write capabilities.
SF-P004  Preparation precedes commitment.
SF-P005  Every action tool has effect verification.
SF-P006  Every financial action has reconciliation.
SF-P007  Public tools are provider-independent where practical.
SF-P008  Provider variants remain internal unless semantics differ.
SF-P009  Search, retrieval and verification remain distinct.
SF-P010  Tool count is not itself a success metric.
SF-P011  Every proposed tool receives a portfolio score.
SF-P012  Every external MCP server receives a federation assessment.
SF-P013  Registry presence does not imply trust.
SF-P014  Official provider servers are preferred where suitable.
SF-P015  External tool inventories are filtered before model exposure.
SF-P016  Generic HTTP and SQL tools are restricted by default.
SF-P017  Generic code execution is sandboxed.
SF-P018  Every high-level agent has mature primitive dependencies.
SF-P019  Composite tools require recurring-sequence evidence.
SF-P020  Agentic backing requires a demonstrated deterministic gap.
SF-P021  Similar tools receive confusion evaluations.
SF-P022  Every tool belongs to a capability ontology.
SF-P023  Every graph receives a restricted domain tool pack.
SF-P024  Full contracts are loaded only after shortlisting.
SF-P025  Unused tools are candidates for deprecation.
SF-P026  Action tools cannot conceal approval-sensitive arguments.
SF-P027  Financial observations include source and timestamp.
SF-P028  Research results include provenance.
SF-P029  Licensed data tools enforce licence and tenant rules.
SF-P030  Database reads and administration remain separate.
SF-P031  Repository writing and merging remain separate.
SF-P032  Drafting and external communication remain separate.
SF-P033  Management recommendations remain distinct from authority.
SF-P034  Domain composites preserve primitive tools where independently useful.
SF-P035  Portfolio growth is evaluated against objective completion.
```

---

# 41. Architectural decision

ServiceFabric should build its portfolio through a capability pyramid.

```text
                Agent-backed services
             investigation and planning

               Composite capabilities
          stable multi-tool domain outcomes

                 Domain primitives
       finance, research, software, projects

               Universal primitives
    retrieval, computation, data, files, code

             Platform and governance
 registry, policy, telemetry, evaluation, lifecycle
```

The lower layers should be narrower, more deterministic and more reusable.

The upper layers should be fewer, more domain-specific and more heavily evaluated.

The recommended first complete vertical slice is:

```text
registry.search_capabilities
        ↓
research.search_papers
        ↓
documents.extract_text
        ↓
research.validate_citation
        ↓
research.build_evidence_set
```

The recommended effectful vertical slice is:

```text
registry.search_capabilities
        ↓
project.search_tasks
        ↓
project.prepare_task
        ↓
approval.create_preview
        ↓
project.create_task
        ↓
effects.verify
```

These two slices jointly validate:

* Discovery
* Primitive composition
* External retrieval
* Evidence
* Agentic backing
* Approval
* Persistent action
* Effect verification
* Maintenance
* Evolution
