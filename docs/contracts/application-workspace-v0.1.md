# Application Workspace Contract v0.1

This contract defines the authoritative directory model, ownership rules, path semantics, and lifecycle boundaries for ServiceFabric Application Workspaces. It guarantees the isolation of user-editable source code from platform-managed runtime state.

## 1. Workspace Roots

The workspace architecture is divided into two explicitly defined roots, controlled by environment variables:

- `SERVICEFABRIC_WORKSPACE`: The visible development root containing editable application source code, shared libraries, and workspace configuration.
- `SERVICEFABRIC_HOME`: The hidden, platform-managed state root containing registry data, resolved bindings, process instances, artifacts, and caches.

**Resolution Rule:**
- If only `SERVICEFABRIC_WORKSPACE` is provided, `SERVICEFABRIC_HOME` defaults to `$SERVICEFABRIC_WORKSPACE/.servicefabric`.
- If neither is provided, `SERVICEFABRIC_WORKSPACE` defaults to the current working directory, and `SERVICEFABRIC_HOME` defaults to the `.servicefabric` directory within it.

## 2. Ownership Classes

Every file and directory within the workspace belongs to exactly one ownership class, dictating how developers and coding assistants interact with it.

### Developer-Owned
*Can be freely edited by humans and coding assistants. Safe to version control.*
- `workspace.yaml`: The stable, portable identity of the workspace.
- `applications/`: Editable application project sources.
- `recipes/`: Reusable application compositions and primitive definitions.
- `libraries/`: Intentionally shared source packages (with their own versioning and dependencies).

### Generated but Application-Local
*Written by ServiceFabric into the developer space. Can be regenerated. Should generally not be manually edited.*
- `applications/<id>/.servicefabric/generated/`: Reverse-proxy configs, generated clients, etc.
- `applications/<id>/.servicefabric/application.lock`: Exact resolved development inputs (framework versions, schema versions).

### Runtime-Owned
*Strictly managed by the ServiceFabric platform. Coding assistants and humans MUST NOT edit these directly.*
- `$SERVICEFABRIC_HOME/*`: Includes all runtime state (see section below).

## 3. Mandatory Workspace Structure

A valid `SERVICEFABRIC_WORKSPACE` must conform to the following layout:

```text
ServiceFabricWorkspace/
├── workspace.yaml
├── applications/
├── recipes/
├── libraries/
└── .servicefabric/
    ├── registry/       # Authoritative projection of known apps and resources
    ├── bindings/       # Resolved mappings from logical requirements to concrete resources
    ├── resources/      # Mutable local resource state (databases, caches, queues)
    ├── runtimes/       # Centrally managed language/runtime foundation profiles
    ├── environments/   # Application-specific dependency environments (e.g., venvs)
    ├── builds/         # Temporary or reproducible build workspaces
    ├── artifacts/      # Immutable application outputs (built packages)
    ├── installations/  # Materialized application revisions prepared for execution
    ├── instances/      # Runtime lifecycle records (PIDs, ports, health)
    ├── logs/           # Bounded and rotatable logs (applications, platform)
    ├── operations/     # Durable-operation state
    ├── locks/          # Filesystem or process locks for state mutation
    ├── cache/          # Rebuildable acceleration data (downloads, indexes)
    ├── tmp/            # Short-lived intermediate data
    └── backups/        # Explicit snapshots of mutable local state
```

## 4. Minimum Application Structure

An empty or generated application project inside `applications/<application-id>/` must contain the following foundational structure:

```text
applications/<application-id>/
├── README.md               # Product-level description (what, who, features)
├── AGENTS.md               # Operating instructions and boundaries for coding assistants
├── ARCHITECTURE.md         # Human-readable architectural description
├── DEVELOPMENT.md          # Executable development guide (commands to run/test)
├── modules/                # Application's primitive modules (frontend, api, worker)
├── tests/                  # Application-level and cross-module integration tests
└── .servicefabric/
    ├── application.yaml    # Declarative application identity
    ├── blueprint.yaml      # How the application was composed (dynamic template inputs)
    ├── bindings.yaml       # Logical resource requirements
    └── development.yaml    # Development commands and expectations (health checks, linting)
```

## 5. Application Identity Rules

A valid `application_id` must conform to the following strict constraints:
- Only lowercase letters, numbers, and single hyphens.
- Length: 3–63 characters.
- Must begin with a letter.
- Must end with a letter or number.

The application directory name MUST exactly match the `application_id` (e.g., `applications/research-notes/`).

## 6. Path-Safety Rules

All platform operations must enforce the following security boundaries:
- Resolved paths must remain strictly inside their declared root (WORKSPACE or HOME).
- Symbolic links must not be followed for generated or runtime-owned paths.
- Path traversal (`../`) is strictly rejected.
- Absolute paths for application IDs are rejected.
- Application creation must fail safely if the target directory already exists.
- Platform state (`SERVICEFABRIC_HOME`) cannot be nested inside an individual application directory (`applications/<id>/`).
- Temporary state writes must use atomic replacement where consistency matters.

## 7. Lifecycle Vocabulary

ServiceFabric defines distinct lifecycle verbs. They must not be conflated:
- **Create**: Generate an editable source project (`applications/<id>/`).
- **Register**: Add the source application to the workspace registry.
- **Build**: Produce build output from source.
- **Publish**: Produce an immutable or stable artifact (stored in `artifacts/`).
- **Install**: Materialize a published artifact for execution (stored in `installations/`).
- **Start**: Create a runtime instance.
- **Stop**: Terminate a runtime instance without deleting source or data.
- **Uninstall**: Remove an installed runtime materialization.
- **Remove**: Remove the editable source application.
- **Purge**: Explicitly remove source, runtime state, bindings, artifacts, and application data.

## 8. Deletion Guarantees

Ambiguous deletion semantics are prohibited. The following guarantees apply:
- Deleting `tmp/` does NOT delete source.
- Deleting `cache/` does NOT delete source or application data.
- Deleting `builds/` does NOT delete published artifacts.
- **Stopping** an application does NOT delete data or source.
- **Uninstalling** an application does NOT delete source.
- **Removing** source (`applications/<id>`) does NOT automatically delete persistent application data.

## 9. Registry Responsibility

The local workspace registry (`$SERVICEFABRIC_HOME/registry/`) is the authoritative source for known applications in the workspace. It is file-backed and records only lightweight facts:
- `application_id`
- `source_path`
- `registration_status`
- `created_time` / `updated_time`

This serves as the source of truth for the local CLI prior to any Django database projection.

## 10. Legacy Boundaries

New workspace applications MUST NOT be created inside the legacy repository directories:
- `3_service_templates/`
- `4_generated_services/`
- `6_service_catalog/`

These locations are deprecated for new applications and remain available solely for backward compatibility with the legacy repository-coupled generation system until a formal migration is completed.