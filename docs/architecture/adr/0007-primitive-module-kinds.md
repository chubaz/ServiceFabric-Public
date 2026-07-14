# ADR 0007: Primitive Module Kinds and Framework Kits

## Status
Accepted

## Context
As ServiceFabric applications grow in complexity, the platform needs a way to reason about and manage different parts of an application (e.g., APIs, frontends, background tasks) without becoming tightly coupled to the specific technologies used to build them (e.g., FastAPI, React, Celery). If the platform requires every application to inherit from a large, monolithic base class, applications become inextricably tied to the platform, making them difficult to write, test, and run independently. Furthermore, we must distinguish between the *operational role* of a component and its *technological implementation*.

## Decision
We will define applications as directed graphs of **Modules**, constructed from **Primitives** and **Framework Kits**.

1. **Primitive (Operational Role):** The smallest reusable operational contract. It describes *how* a module behaves inside the platform (e.g., how it is built, started, checked for health, and stopped), not its business logic or framework.
   - The initial set of primitives is strictly limited to:
     - `service`: Long-running process exposing an interface (e.g., HTTP/RPC).
     - `web`: Browser-facing interface compiled or served to a user.
     - `worker`: Long-running background consumer of messages/tasks.
     - `job`: Finite process that runs, produces a result, and exits.
     - `library`: Shared code imported by other modules, having no independent process.

2. **Framework Kit (Technological Implementation):** Makes a primitive executable. A kit (e.g., `fastapi-service`, `react-web`) provides the build adapter, start adapter, health convention, and configuration generator for a specific technology. Framework kits implement a standard behavior interface (e.g., `build()`, `start()`, `health()`, `stop()`) rather than requiring applications to subclass platform base classes.

3. **Module (Application-Specific Use):** An instance of a primitive and kit within a specific application (e.g., an `api` module of kind `service` using the `fastapi-service` kit).

4. **Application Graph:** Applications are assembled by connecting modules using interface edges (provided/required interfaces), resource edges (database/queue bindings), and lifecycle edges (start order). A development supervisor orchestrates the graph during local development.

## Consequences
- **Loose Coupling:** Applications remain ordinary framework projects (e.g., standard FastAPI or React apps) understandable by coding assistants and runnable outside ServiceFabric.
- **Platform Simplicity:** The platform only needs to understand the five core primitives, regardless of how many new technologies or framework kits are added.
- **Clear Boundaries:** Modules communicate through documented interfaces and bindings, not by importing internal implementation details across module boundaries.
- **Evidence-Driven Evolution:** New framework kits are only added when proven by extracting patterns from working reference applications.