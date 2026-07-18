# Ownership model

| Lane | Branch | Owned paths |
|---|---|---|
| evidence | `agent/w10-evidence` | application-evidence package, tests, handoff |
| capability-distillation | `agent/w10-capability-distillation` | capability-distillation package, tests, handoff |
| technique-policies | `agent/w10-technique-policies` | technique-policies package, tests, handoff |
| engineering-distillation | `agent/w10-engineering-distillation` | engineering-distillation package, tests, handoff |
| evolution-proposals | `agent/w10-evolution-proposals` | evolution-proposals package, tests, handoff |
| release-readiness | `agent/w10-release-readiness` | release package, release docs, README, tests, handoff |
| evaluation | `agent/w10-evaluation` | one Wave-10 journey, fixtures, handoff |
| integration | `integration/phase25-wave10` | shared contracts, composition, CLI, publication adapters, locks, Makefile/CI, review, closure |

Specialists modify only their owned paths and never merge their branch. Integration reviews exact candidate commits and alone reconciles cross-cutting changes.
