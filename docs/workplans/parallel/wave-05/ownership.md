# Wave-5 Ownership

| Lane | Owned scope |
| --- | --- |
| integration | Application-status bridge, CLI, Makefile/CI, dependency locks, cross-package composition, candidate review, and completion integration |
| availability | `packages/servicefabric_capability_runtime/**`, `tests/capability_runtime/**`, and its canonical handoff; availability only, maximum four focused tests |
| invocation | `packages/servicefabric_capability_invocation/**`, `tests/capability_invocation/**`, and its canonical handoff; invocation core without HTTP implementation, maximum four focused tests |
| http-adapter | `packages/servicefabric_http_operation_adapter/**`, `tests/http_operation_adapter/**`, and its canonical handoff; reviewed loopback HTTP transport only, maximum three focused tests |
| acceptance | `tests/wave_05/**`, `tests/fixtures/wave_05/**`, and its canonical handoff; one end-to-end journey, maximum two tests |

Specialists create focused candidate commits and never merge, rebase, cherry-pick, or pull another feature branch. The integration lane reviews and composes candidates but does not implement specialist feature functionality.
