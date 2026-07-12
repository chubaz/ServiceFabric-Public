# ServiceFabric Refactoring Programme

Last updated: 2026-07-12
Programme source: `../ServiceFabric Formal Refactoring Plan for Codex.md`

## Purpose

This repository-local programme tracks the formal pull-request sequence without widening scope. It exists to keep each refactoring wave independently reviewable and traceable to canonical specifications and ADRs.

## Global constraints

- Do not change runtime behaviour during `P0-00`.
- Do not edit application code during `P0-00`.
- Do not begin `P0-01` in this pull request.
- Keep the existing numbered directories in place during `P0`.
- Cite `SF-SPEC-*` and `ADR-*` identifiers in future pull requests.

## Sequence status

| PR | Title | Status | Scope |
| --- | --- | --- | --- |
| `P0-00` through `P0-06` | P0 containment and production baseline | completed | Completed in merged pull requests through reproducible Python dependency builds. |
| `C1-00` | Canonical contract package foundation | completed | Established framework-neutral `ServicePackageDefinition` contracts, schema export, fixtures, and CI without runtime integration. |
| `C1-01` | Canonical tool lifecycle contracts | current | Define `ToolDefinition`, immutable revisions, desired deployments, observed status, fixtures, schemas, and contract CI. |
| `C1-02` | Contract validation integration | not started | Not started. |
| `C1-03` | Contract publication workflow | not started | Not started. |
| `C1-04` | Contract migration preparation | not started | Not started. |

## `P0-00` deliverables

- `docs/architecture/specification-map.md`
- `docs/architecture/adr/0001-mcp-is-an-optional-projection.md`
- `docs/architecture/adr/0002-service-package-versus-tool-operation.md`
- `docs/architecture/adr/0003-legacy-flask-strangler-strategy.md`
- `docs/architecture/adr/0004-one-schema-owner-per-table.md`
- `docs/refactoring/programme.md`
- `docs/refactoring/debt-register.yaml`
- `scripts/architecture/check_legacy_patterns.py`
- `tests/architecture/test_repository_boundaries.py`
- `.github/workflows/refactoring-ci.yml`

## Exit criteria for `P0-00`

- Canonical specification locations and hashes are recorded.
- Architectural decisions have repository-local ADRs with dates and status.
- Known unsafe legacy patterns are explicitly registered as debt.
- Automated checks reject new occurrences of prohibited legacy patterns.
- CI runs the architecture checks and repository-boundary tests.

## Deferred until `P0-01`

No containment, endpoint protection, token validation, CORS changes, container hardening, or runtime behaviour changes are included in this pull request.
