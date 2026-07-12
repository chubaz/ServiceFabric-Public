# V3-00 — Governance and Durable Operations

## Status

Current.

## Objective

Define and implement the first bounded ServiceFabric governance and durable-operation vertical slice over the canonical tool, application, artifact, and capsule foundations established through V2-01.

The milestone must provide a controlled lifecycle resembling:

```text
canonical request
        ↓
policy evaluation
        ↓
approval decision where required
        ↓
durable operation acceptance
        ↓
bounded execution attempt
        ↓
evidence and effect verification
        ↓
completion, failure, cancellation, timeout, or reconciliation
```

Accepted durable work must remain observable after the process that accepted it terminates.

Governance decisions, approval bindings, operation state, evidence references, and verified effects must remain distinct canonical resources.

## Initial scope

V3-00 will define:

* canonical policy-evaluation inputs and decisions;
* authority and risk classification;
* approval requests, decisions, and immutable approval bindings;
* durable operation acceptance and state transitions;
* a bounded local durable operation store;
* optimistic concurrency or equivalent transition protection;
* idempotency and duplicate-request handling;
* cancellation, timeout, and retry rules;
* reconciliation for uncertain external effects;
* persistent evidence and effect-receipt references;
* an internal governance and operations service boundary;
* Python client and bounded CLI operations;
* architecture and security guardrails;
* executable completion verification.

## Governing principles

### Default deny

Operations requiring authority that has not been established must not execute.

Missing, expired, mismatched, or revoked approval must fail closed.

### Immutable decisions and mutable operational state

Policy decisions and approval decisions are immutable records.

Operation status may evolve only through explicit validated transitions.

Historical operation events must not be rewritten to simulate a different execution history.

### Effectively-once effects

Infrastructure may retry work, but committed external effects must be protected through:

* idempotency digests;
* immutable approval bindings;
* effect receipts;
* read-after-write verification where appropriate;
* reconciliation before uncertain retries.

### No authority from serialization

Caller-provided JSON is not evidence of identity or permission.

Only trusted adapters may construct authenticated caller and authority context.

### Persistence behind a canonical boundary

The initial durable store may be local and file-backed, but canonical governance and operation contracts must not depend on filesystem layout.

Production PostgreSQL, distributed queues, and multi-region infrastructure remain deferred.

## Constraints

V3-00 must not introduce:

* a production identity provider;
* a public multi-tenant control plane;
* unrestricted administrative authority;
* arbitrary shell or subprocess execution;
* irreversible production actions;
* distributed workers or durable event-bus infrastructure;
* Kubernetes deployment orchestration;
* production PostgreSQL migrations;
* modifications to legacy Django migrations;
* Compose or Nginx topology changes;
* production secret-management infrastructure;
* V4-00 MCP gateway or MCP projection work;
* automatic execution when required approval is missing;
* retries of uncertain effects before reconciliation;
* mutation of immutable policy or approval records.

## Starting baseline

V3-00 starts after:

```text
E0-00 completed
V1-00 completed
V1-01 completed
V2-00 completed
V2-01 completed
V2-01 CI portability correction merged
```

The existing `ServiceFabricOperation`, cancellation, evidence, observed-effect, and effect-receipt contracts are the baseline rather than disposable prototypes.

## Next action

Expand this placeholder into the complete V3-00 implementation workplan before writing governance, approval, persistence, or durable-operation code.
