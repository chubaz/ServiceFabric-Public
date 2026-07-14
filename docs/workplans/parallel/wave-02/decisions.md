# Wave-2 Decisions

- The local development supervisor owns orchestration, not framework execution or resource provisioning.
- Runtime bindings are application-scoped and must be idempotent, isolated, persisted, describable, and releasable.
- Framework kits emit reviewed bounded launch plans; they do not start subprocesses.
- The reference application is ordinary modular application source and owns product behavior and acceptance specifications.
- AP-00C remains the managed-process owner. Wave 2 composes it and does not duplicate it.
