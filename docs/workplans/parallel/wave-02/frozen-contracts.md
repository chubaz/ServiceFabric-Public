# Wave-2 Frozen Contracts

Before specialist launch, freeze only these shared boundaries:

- `docs/contracts/application-module-v0.1.md`
- `schemas/servicefabric/local/v1/**`
- `packages/servicefabric_application_model/**`
- `packages/servicefabric_application_assembly/**`
- `packages/servicefabric_process_runtime/**`
- `packages/servicefabric_workspace/**`

They define module manifests, deterministic assembly, managed process lifecycle, and local workspace isolation. Framework runtime planning, resource-provider implementation, the supervisor, and the reference application remain lane-owned.

After launch, a frozen-contract change requires a written Contract Change Request, integration approval, a committed decision, a new integration base, and synchronization only for affected lanes.
