# ServiceFabric Agent Instructions

## Repository purpose

ServiceFabric is a heterogeneous application and tool hosting platform with canonical package, tool, invocation, result, evidence, effect, and operation contracts.

## Stable architecture rules

- `ServicePackageDefinition` is not `ToolDefinition`; a package may implement zero, one, or many tools.
- MCP is an optional projection, not the runtime substrate or implementation owner.
- Consumer adapters contain no tool business logic.
- Canonical calls use `ToolInvocationRequest` and `ToolResult`.
- `ToolRevision` is immutable.
- Secrets are opaque references, never literal contract values.
- Legacy dynamic execution remains contained.
- New execution paths must not bypass the canonical runtime.

## Repository map

- Canonical specifications: `docs/canonical/`; source map: `docs/architecture/specification-map.md`.
- Decisions: `docs/architecture/adr/`; contract guides: `docs/contracts/`.
- Contracts and schemas: `packages/servicefabric_contracts/` and `schemas/servicefabric/`.
- Current scope: `docs/workplans/current.md`; machine rules: `config/agent/milestones.json`.
- Boundaries: `tests/architecture/`; legacy runtime: numbered service directories.
- Future packages and services must be introduced only by the current workplan.

## Standard execution workflow

1. Read this file and `docs/workplans/current.md`.
2. Run `make agent-preflight`.
3. Implement only the current milestone and update status after logical commits.
4. Run focused tests while working and `make verify-current` before completion.
5. Run `make agent-handoff`.
6. Report blockers, deviations, limitations, concise validation, and rollback.

## Stable prohibitions

- No mass formatting, unrelated dependency upgrades, arbitrary dynamic imports, shell execution, or SQL execution.
- No raw credentials or automatic trust of remote MCP inventory.
- No framework migration outside milestone scope and no weakening architecture tests.
- Do not edit generated schema snapshots by hand.

## Context efficiency

- Do not restate documents, produce long pre-implementation essays, or repeat successful test output.
- Use the paths listed by the workplan and `make agent-context`; avoid unrestricted repository searches.
- Do not reread canonical documents while recorded hashes remain valid.
