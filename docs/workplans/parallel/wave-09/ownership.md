# Ownership model

| Lane | Branch | Owned paths |
|---|---|---|
| technology-profile | `agent/w9-technology-profile` | `packages/servicefabric_technology_profiles/**`, `tests/technology_profiles/**`, handoff |
| blueprint-compiler | `agent/w9-blueprint-compiler` | `packages/servicefabric_engineering_blueprints/**`, `tests/engineering_blueprints/**`, handoff |
| factory-lifecycle | `agent/w9-factory-lifecycle` | `packages/servicefabric_application_factory_state/**`, `tests/application_factory_state/**`, handoff |
| repository-bootstrap | `agent/w9-repository-bootstrap` | `packages/servicefabric_application_factory_bootstrap/**`, `tests/application_factory_bootstrap/**`, handoff |
| candidate-review | `agent/w9-candidate-review` | `packages/servicefabric_application_candidate_review/**`, `tests/application_candidate_review/**`, handoff |
| application-integration | `agent/w9-application-integration` | `packages/servicefabric_application_integration/**`, `tests/application_integration/**`, handoff |
| evaluation | `agent/w9-evaluation` | `tests/wave_09/**`, `tests/fixtures/wave_09/**`, handoff |
| integration | `integration/phase25-wave9` | shared contracts, composition, CLI, locks, Makefile, CI, candidate integration, closure |

Integration alone reconciles cross-cutting changes. Specialist lanes do not modify another lane’s owned paths. The factory delegates provider execution to Wave-8 and never embeds provider business logic in consumer adapters.
