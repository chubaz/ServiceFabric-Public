# Wave-3 Ownership

| Lane | Owned paths | Boundary |
| --- | --- | --- |
| generator | `packages/servicefabric_application_generator/**`, `packages/servicefabric_blueprints/**`, `tests/application_generator/**`, its handoff | Blueprint materialization and application creation only |
| application-builder | `packages/servicefabric_application_builder/**`, `tests/application_builder/**`, its handoff | Deterministic build coordination and artifact manifests only |
| agent-guidance | `packages/servicefabric_agent_guidance/**`, `tests/agent_guidance/**`, its handoff | Generated guidance and documentation only |
| acceptance | `tests/wave_03/**`, `tests/fixtures/wave_03/**`, its handoff | Acceptance tests and fixtures only |
| integration | Shared controls, CLI, CI, locks, composition, and acceptance | Candidate review and final integration |

Specialists create focused candidate commits only. They do not merge, rebase, pull other feature branches, or edit shared controls.
