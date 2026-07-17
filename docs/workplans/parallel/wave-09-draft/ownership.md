# Draft ownership model

This ownership model applies only to producing and reviewing Wave-9 draft material. No lane is authorized to create implementation packages, services, clients, tests, dependencies, CI, or provider executions.

| Lane | Draft responsibility | Draft-owned output |
|---|---|---|
| blueprint-compiler | Task-DAG and application-blueprint design | engineering blueprint amendments |
| technology-profile | Reviewed-kit selection and compatibility-gate design | technology-profile amendments |
| factory-bootstrap | Lifecycle state, approval, escalation, and factory bootstrap design | lifecycle amendments |
| application-integration | Candidate review, integration authority, and closure design | integration-order amendments |
| evaluation | Research Workspace OS evaluation and recovery measures | verification amendments |
| integration | Cross-draft coherence and final draft acceptance | all Wave-9 draft docs and manifests |

Integration is the only lane allowed to reconcile cross-cutting draft decisions. Specialist proposals must not alter another specialist’s draft-owned document without integration review.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** future execution ownership can be delegated to a provider runtime only after Wave-8 is closed. Until then, all Wave-9 lane ownership is documentation and manifest design, not an authorization to invoke providers or claim runtime behavior.
