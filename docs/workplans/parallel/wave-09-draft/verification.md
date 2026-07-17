# Draft verification and evaluation

The draft is reviewed for internal coherence, not implementation correctness. Acceptance checks are: all requested documents and manifests exist; task responsibilities are disjoint; no draft manifest authorizes implementation paths; all lifecycle stages have an authority and escalation path; technology profiles select only reviewed kits; and every runtime claim is either contract-backed or labeled as a Wave-8-dependent assumption.

The evaluation exemplar is Research Workspace OS: a create intent decomposed into workspace model, ingestion/search, UI/export, and integration verification. Proposed measures are plan completeness, blocked-task rate, task success rate, verification coverage, change-scope compliance, evidence traceability, provider duration, token consumption, estimated cost, and recovery rate for timeout/unknown/cancelled outcomes.

Failure cases retain blockers and artifacts, reject unverified candidates, and require an explicit retry/reconciliation decision. End-to-end elapsed time, cancellation latency, retry correlation, budget enforcement, and artifact integrity require dedicated future instrumentation.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** provider result status, usage, event/stderr artifact references, timeout/unknown/cancelled outcomes, and policy limits are populated and operationally reliable enough to evaluate. Cost is only an estimate; retry correlation, enforcement, and cancellation propagation are not established by the public contracts and remain gated on Wave-8 closure.
