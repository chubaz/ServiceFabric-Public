# Application Module Contract v0.1

This contract defines the taxonomy, schemas, and operational behavior of ServiceFabric Primitives, Framework Kits, and Modules. It establishes how applications are modeled as directed graphs of independent, loosely coupled modules rather than monolithic codebases.

## 1. Core Taxonomy

ServiceFabric applications are composed using three distinct concepts:

### Primitive (Operational Role)
A primitive is the smallest reusable operational contract. It describes *how* a module behaves within the platform lifecycle—not its business logic, and not its framework.
The platform recognizes exactly five primitives:
- **`service`**: A continuously running process that exposes an interface (e.g., HTTP, RPC) and accepts requests.
- **`web`**: A browser-facing interface that is either compiled to static assets or served dynamically to a user.
- **`worker`**: A continuously running background process that consumes messages or tasks from a queue or stream.
- **`job`**: A finite process that starts, performs a discrete unit of work, produces a result (exit code), and terminates.
- **`library`**: Shared application code that is imported by other modules. It has no independent runtime process.

### Framework Kit (Technological Implementation)
A framework kit makes a primitive executable using a specific technology stack (e.g., `fastapi-service`, `react-web`, `python-worker`). A kit provides:
- Build and start adapters.
- Health check conventions.
- Environment configuration generators.
- Logging integration.
- Scaffold definitions and coding assistant guidance fragments.

*Rule: Primitives are programmed as behavior contracts (Protocols/Interfaces), not as heavy base classes. Applications built with a kit remain ordinary framework projects (e.g., a standard FastAPI app).*

### Module (Application-Specific Instance)
A module is the concrete application-specific use of a primitive and a kit.
*Example: An `api` module of kind `service` using the `fastapi-service` kit.*

## 2. Common Module Contract

Every primitive module is described using a consistent `ApplicationModule` manifest (typically stored as `module.yaml` in the workspace). It answers operational questions without defining business logic:

```yaml
apiVersion: servicefabric.local/v1
kind: ApplicationModule

metadata:
  id: api
  version: 0.1.0

spec:
  primitive: service
  kit: fastapi-service@1.0

  provides:
    - id: notes-api
      type: http

  requires:
    interfaces:
      - id: notes-domain
    bindings:
      - database.primary

  lifecycle:
    startAfter:
      - database.primary
    readiness:
      type: http
      path: /health/ready
    shutdown:
      timeoutSeconds: 10

  resources:
    memoryMiB: 256
```

## 3. The Application Graph

Applications are assembled as directed graphs where nodes are **Modules** and edges are **Dependencies**. The platform assembler resolves three types of edges:
1. **Interface Edges:** A module consumes an interface (HTTP, package, etc.) provided by another module. *(Rule: Modules must never import internal files from another module; they must consume declared interfaces/libraries.)*
2. **Resource Edges:** A module requires a ServiceFabric resource binding (e.g., database, queue).
3. **Lifecycle Edges:** A module cannot start until another dependency (module or resource) reports readiness.

### Graph Assembly Sequence
The platform development supervisor performs the following sequence to run an application:
1. Load application blueprint and module definitions.
2. Resolve framework kits.
3. Validate provided and required interfaces and bindings.
4. Detect missing dependencies and cycle errors.
5. Calculate topological build order.
6. Calculate topological startup order.
7. Generate development configuration (injecting environment variables for ports and bindings).

## 4. Primitive Conformance

Framework kits must pass conformance suites proving they fulfill their primitive's operational contract:
- **Service Conformance:** Must build, start on an allocated port, report readiness, accept requests, stop cleanly, and emit structured logs.
- **Web Conformance:** Must install dependencies, run a development server, receive injected API configuration, build static output, and report readiness.
- **Worker Conformance:** Must connect to a queue/source, process messages, report heartbeats, and stop gracefully.
- **Job Conformance:** Must receive bindings, execute once, return an exit status, and fail safely.
- **Library Conformance:** Must build as a package, run tests, and safely be consumed by other modules without attempting to start a process.

## 5. Development Supervisor

During local development, modules are orchestrated by a Development Supervisor (`servicefabric apps dev ...`). The supervisor is responsible for:
- Preparing dependency environments (e.g., Python venvs, Node modules).
- Allocating dynamic local ports.
- Injecting standard environment variables (e.g., `SF_MODULE_PORT`, `SF_DATABASE_PRIMARY_URL`).
- Starting modules in dependency order.
- Observing module health and capturing logs.
- Allowing individual module restarts (e.g., `servicefabric apps dev restart api`) without rebuilding unaffected parts of the graph.
