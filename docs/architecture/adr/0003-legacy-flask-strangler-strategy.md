# ADR 0003: Legacy Flask Strangler Strategy

Status: Accepted
Date: 2026-07-11

## Context

The fit-for-purpose assessment classifies the current Flask dynamic execution path as a legacy host that must not become the canonical tool runtime. The formal plan requires containment before behavioural refactoring starts.

## Decision

Existing Flask services form a temporary legacy application host.

No new tools may depend on dynamic Flask execution.

Migration follows a strangler pattern.

## Consequences

Legacy dynamic import and dynamic script execution remain documented debt, not approved extension points.

Architecture checks must reject new occurrences of the known legacy execution patterns.

Future PRs should cite `SF-SPEC-002`, `SF-SPEC-007`, `SF-SPEC-010`, and the fit-for-purpose assessment.
