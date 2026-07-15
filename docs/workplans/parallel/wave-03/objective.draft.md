# Wave-3 Objective Draft

## Objective

Define the next validated increment after Wave 2. The integration authority must replace this draft with a bounded delivery objective before contract freeze and specialist launch.

## Lanes And Owned Paths

| Lane | Draft ownership |
| --- | --- |
| integration | shared contracts, composition, CLI, Makefile, CI, locks, acceptance, closure |
| supervisor | `services/application_dev_supervisor/**`, `tests/application_dev_supervisor/**` |
| runtime-bindings | `packages/servicefabric_resource_bindings/**`, `tests/resource_bindings/**` |
| kit-execution | `packages/servicefabric_framework_kits/**`, `packages/servicefabric_blueprints/**`, related tests |
| reference-app | `examples/research-notes/**`, `tests/wave_03/**` |

## Frozen Contracts

Freeze only the shared module, assembly, process-runtime, workspace, and explicitly approved cross-lane contract paths required by the selected objective. Any later change requires a Contract Change Request, integration approval, committed decision, new base, and affected-lane synchronization.

## Acceptance Journey

The final journey must be specified before launch and prove the selected user-visible outcome end to end, including deterministic behavior, safe invalid cases, lifecycle cleanup, and preservation of Wave-1 and Wave-2 regressions.

## Exclusions

No automatic merges, force pushes, branch or worktree deletion, remote execution, production deployment, containers, distributed resources, capability publication, or MCP expansion unless a future approved objective explicitly includes them.
