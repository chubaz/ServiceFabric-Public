# Local Application Hosting Baseline Contract

This contract freezes the stable local application hosting baseline proven by AP-01A. Future modularization, refactoring, or architectural evolution of the ServiceFabric hosting layer must preserve these foundational guarantees.

## Foundational Guarantees

Any compliant implementation of the local application hosting layer must support and preserve the following lifecycle phases:

### 1. Isolated Workspace Initialization (`init`)
- Must establish a clean, isolated directory structure (`SERVICEFABRIC_HOME`).
- Initialization must be reproducible and safe to execute against an already-initialized directory without corrupting state.

### 2. Idempotent Installation (`apps install`)
- Installing a reviewed application package from a source directory must succeed deterministically.
- Installation must be idempotent: repeated installation of the same package path must be handled safely (e.g., reporting "Already installed") without side-effects or duplication.

### 3. Deterministic Immutable Build (`apps build`)
- Building an installed application must produce an immutable, verified build artifact with a unique content digest (SHA-256).
- Repeated builds of the same unmodified source code must produce the identical artifact digest.
- Builds must fail safely if the source code contains syntax errors or invalid declarations.

### 4. Managed Process Lifecycle (`apps start` / `apps stop`)
- Starting an application must launch exactly one managed, owned subprocess bound to loopback.
- Process execution must be fully tracked. Multiple start invocations must safely resolve to or preserve the single running process.
- Stopping an application must reliably terminate the owned subprocess, preventing any orphan processes or stale pid signals.
- Stop operations must be idempotent: repeated stops on a stopped application must succeed safely without errors or tracebacks.

### 5. Continuous Health Monitoring (`health`)
- The hosting engine must verify application startup and ongoing health (e.g., using loopback HTTP health check probes).
- The application state must transition to `healthy` only after positive validation, and fail safely/report `failed` if health checks timeout or exit unexpectedly.

### 6. Decoupled Resource Observation (`apps resources`)
- Resource observation must be capable of measuring and reporting runtime statistics of the managed application.
- The output structure must strictly separate **declared resource expectations** (e.g., memory limits) from **measured current and peak resource consumption** (e.g., measured RSS bytes, CPU percentages).

### 7. Safe Failure and Error Isolation
- Commands must not leak Python tracebacks to the CLI user interface under error conditions (e.g., invalid configurations, missing applications, or abnormal process terminations).
- Stale process IDs or corrupt local state must be detected and handled gracefully without impacting unrelated system operations.

## Hosting-Only Boundary

The hosting contract is strictly bounded at "application successfully hosted, monitored, and observed". It has no dependency on, and does not require:
- Tool listing or description capability.
- Capability publication or registration.
- Canonical service or capability invocations (`servicefabric call`).
- MCP gateway, projection, or agentic workflow integrations.

These upper-layer capabilities are built on top of this hosting baseline but do not define its validity.
