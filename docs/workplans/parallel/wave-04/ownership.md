# Wave-4 Ownership

| Lane | Owned scope |
| --- | --- |
| integration | Shared contracts and decisions, CLI integration, Makefile/CI, locks, cross-package composition, `tests/wave_04`, candidate review and completion integration |
| operation-model | `OperationDefinition`, identity/versioning, application/module/interface references, schemas, bounded HTTP bindings, strict loading and serialization |
| capability-model | `CapabilityDefinition`, exact operation references, stable semantics, contracts, effects, strict loading and serialization |
| capability-registry | Atomic static file-backed registry, idempotency/conflict handling, digest, indexing, and path safety |
| capability-authoring | Explicit Research Notes declarations and generator support for local operation/capability manifests |

The integration lane must not implement the specialist feature packages.
