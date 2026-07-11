# ADR 0002: Service Package Versus Tool Operation

Status: Accepted
Date: 2026-07-11

## Context

The formal plan corrects the platform model by separating a hosted package from a bounded callable tool operation. Existing repository structures mix frontends, APIs, workers, and runtime assumptions.

## Decision

`ServicePackageDefinition` describes a hosted or referenced package.

`ToolDefinition` describes a bounded callable operation.

One package may implement zero, one, or many tools.

## Consequences

P0 documentation must use package-oriented language for deployable units and tool-oriented language for machine-callable operations.

Future contract work must avoid forcing frontend-only or CLI-only packages into the tool model.

Future PRs should cite `SF-SPEC-001`, `SF-SPEC-002`, and `SF-SPEC-011`.
