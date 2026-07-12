# V2-01 — Capsule Hosting and Authoring

## Status

Current.

## Objective

Define reviewed capsule-authoring resources and a bounded capsule-hosting
lifecycle on top of immutable V2-00 application artifacts.

## Initial scope

V2-01 will define:

- canonical capsule definitions and immutable revisions;
- reviewed authoring inputs;
- capsule-to-artifact bindings;
- bounded host sessions;
- deterministic route and asset resolution;
- loopback-only or otherwise explicitly bounded hosting;
- Python client and CLI operations;
- architecture and security guardrails;
- executable completion verification.

## Constraints

V2-01 must not introduce:

- arbitrary code execution;
- unrestricted shell or subprocess execution;
- user-authored Dockerfiles;
- production deployment orchestration;
- public multi-tenant hosting;
- database-backed registry infrastructure;
- unrestricted filesystem access;
- dynamic backend application hosting;
- Compose, Nginx, or Django migration changes.

## Next action

Expand this placeholder into the complete V2-01 implementation workplan before
writing capsule-hosting or authoring code.