# ADR 0006: External Multi-Application Workspaces

## Status
Accepted

## Context
ServiceFabric originally generated and stored application code within the platform repository itself (e.g., `3_service_templates`, `4_generated_services`, `6_service_catalog`). Concurrently, the newer `servicefabric` CLI operated entirely inside a `SERVICEFABRIC_HOME` directory, using it exclusively for platform-managed state (artifacts, operation data, configuration) but providing no formal structure for human-readable application source code.

This created conflicting models: one entangled application source with platform code, while the other provided a state directory unsuitable for coding assistants or version control of source files. If the repository-coupled approach were extended, application creation would continue to mutate the platform repository, making upgrades complex and increasing the risk of coding assistants accidentally modifying core ServiceFabric platform code.

## Decision
We will adopt a hybrid **external workspace architecture**.

The ServiceFabric platform will introduce an external multi-application development workspace with a hidden platform state area. The fundamental separation is:
- **ServiceFabric platform code** (ServiceFabric-Public repository) ≠ **Application source code** (User Workspace) ≠ **Platform-managed runtime state** (Hidden `.servicefabric` directory in User Workspace)

### 1. The Workspace Directory (`SERVICEFABRIC_WORKSPACE`)
This is the visible, user-facing area where applications are designed and coded. It contains:
- `workspace.yaml` (Workspace identity and stable configuration)
- `applications/` (Editable application projects)
- `recipes/` (Reusable application compositions)
- `libraries/` (Intentionally shared source packages)

### 2. The Platform-Managed State Directory (`SERVICEFABRIC_HOME`)
This is the hidden, operational area containing all runtime-managed state. It defaults to `$SERVICEFABRIC_WORKSPACE/.servicefabric/` and contains directories like `registry/`, `bindings/`, `resources/`, `runtimes/`, `environments/`, `builds/`, `artifacts/`, `installations/`, `instances/`, `logs/`, `operations/`, `locks/`, `cache/`, `tmp/`, and `backups/`.

### Rejected Options
- **Continue generating applications inside the repository:** Rejected because it mutates the platform repository, confuses platform upgrades with application changes, and risks coding assistants modifying core code.
- **Put everything under `SERVICEFABRIC_HOME` without separation:** Rejected because editable source code would become mixed with artifacts, caches, and process IDs, exposing runtime internals to coding assistants and complicating backups.
- **One independent Git repository per application initially:** Rejected because it creates excessive operational burden for small personal applications and complicates local shared libraries (though the workspace structure supports this natively in the future).

## Consequences
- **Clear Isolation:** Coding assistants have a clear operating boundary (`applications/<id>`) protected from platform internals.
- **Safe State:** Platform state is protected in a hidden directory.
- **Portability:** The external workspace can be backed up or managed in version control without dragging along the platform repository or disposable runtime state.
- **Legacy Migration:** Existing repository generation paths (`3_service_templates`, `4_generated_services`, `6_service_catalog`) are deprecated for new applications but retained temporarily until a full migration occurs.
- **Tooling:** All ServiceFabric CLI commands, builders, and hosts must be updated to resolve paths through a unified workspace package rather than hardcoding relative or absolute directories.