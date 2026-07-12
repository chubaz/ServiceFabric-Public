# V1-00 Core Tool Platform

## Objective

Deliver the first trusted vertical slice: ToolsetDefinition and portfolio contracts, a file-backed deterministic portfolio resolver, canonical invocation kernel, internal runtime service, Python client/CLI, and native `math.calculate`.

## Starting conditions and governance

Start from merged E0-00 with clean preflight. Follow ADR-0001, ADR-0002, ADR-0005 and contract guides under `docs/contracts/`. Preserve C1 resources and protocol neutrality.

## Scope

Allowed paths are committed in `config/agent/milestones.json`. Deliver contracts and schemas, portfolio fixtures/resolver, invocation kernel, internal service boundary, client/CLI, math vertical slice, tests and focused documentation. Suggested commits: contracts; portfolio; kernel; service; client/CLI; math; tests/CI/docs.

Forbidden: external MCP, LangChain/LangGraph, composite graphs, Pi extensions, application builder, Django authoring/database registry, durable operations, MCP gateway, workstation mutation tools, unrelated runtime changes.

## Acceptance and verification

Deterministic portfolio resolution; canonical request/result flow; immutable revision selection; trusted bounded math execution; no dynamic imports or arbitrary commands; protocol-neutral tests; readiness and completion verification pass. Stop on canonical hash drift, scope conflicts, raw credentials, arbitrary execution, or required database/runtime migration.

Completion report must give changed areas, contract/schema hashes, focused validation, deviations, limitations and rollback. Rollback is a PR revert with no data migration. Next milestone: V1-01 agent and external-tool integrations.
