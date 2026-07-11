# ADR 0001: MCP Is an Optional Projection

Status: Accepted
Date: 2026-07-11

## Context

The formal refactoring plan requires P0 to stop the repository from treating MCP as the owner of tool implementation. The canonical architecture separates internal ServiceFabric contracts from MCP exposure and treats the gateway as a projection boundary.

## Decision

MCP is an external protocol projection.

The gateway does not define or own tool implementation.

A package may exist without MCP exposure.

## Consequences

Repository documentation and future refactoring must keep implementation, hosting, and exposure as separate concerns.

P0 must not add new MCP exposure paths.

Future contract and runtime PRs must cite `SF-SPEC-001`, `SF-SPEC-002`, and `SF-SPEC-011`.
