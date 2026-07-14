# Wave-2 Objective

Wave 2 delivers a local development supervisor for the modular Research Notes application. It loads manifests and a deterministic assembly plan, resolves resources, prepares modules, starts executable modules in dependency order, waits for readiness, reports aggregate state, supports bounded logs and observations, restarts only the API, preserves SQLite data, and shuts down without stale process, lock, port, or temporary runtime state.

Excluded: capabilities, MCP publication, remote execution, containers, distributed resources, and production deployment.

The accepted base is `715de644eff2ee003469f14d574c4b70706bc70a`.
