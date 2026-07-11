# ADR 0004: One Schema Owner Per Table

Status: Accepted
Date: 2026-07-11

## Context

The formal refactoring plan prohibits cross-service ORM ownership and requires one schema owner and one migration system per table. The current repository contains multiple frameworks and template paths that should not share uncontrolled schema authority.

## Decision

Each table has one schema owner and one migration system.

Cross-service ORM ownership is prohibited.

## Consequences

Future refactoring must remove implicit schema creation and avoid introducing duplicate table ownership across Django, Flask, FastAPI, or templates.

Architecture checks must flag new plaintext token fields and other schema shortcuts that would deepen cross-service ownership ambiguity.

Future PRs should cite `SF-SPEC-001`, `SF-SPEC-007`, and `SF-SPEC-011`.
