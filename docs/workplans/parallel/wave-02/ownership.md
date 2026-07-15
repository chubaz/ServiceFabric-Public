# Wave-2 Ownership

| Lane | Owned paths | Excludes |
| --- | --- | --- |
| supervisor | `services/application_dev_supervisor/**`, `tests/application_dev_supervisor/**` | CLI, providers, framework kits |
| runtime-bindings | `packages/servicefabric_resource_bindings/**`, `tests/resource_bindings/**` | supervisor, CLI |
| kit-execution | framework kits, blueprints, their tests | subprocess ownership, arbitrary commands |
| reference-app | `examples/research-notes/**`, `tests/wave_02/**` | framework and supervisor internals |
| integration | frozen contracts, composition, CLI, Makefile, CI, locks, acceptance | competing specialist subsystem |

Specialists may make focused candidate commits only. They may not merge, rebase, cherry-pick another lane, pull a feature branch, or modify shared CLI, CI, Makefile, locks, or milestone state.
