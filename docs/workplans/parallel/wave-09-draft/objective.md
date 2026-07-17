# Wave-9 draft objective: Autonomous Application Factory

Prepare the design authority, task topology, and evaluation criteria for an Autonomous Application Factory. The factory will turn a bounded `ApplicationIntent` into an approved application blueprint, isolated candidate work, reviewed integration, and a closure handoff. This is a planning draft only: it authorizes no package, service, client, test, dependency, CI, or runtime change.

The draft preserves canonical ServiceFabric boundaries: application intent and task results remain canonical; provider adapters remain projections behind the provider runtime; the integration authority alone accepts application-level candidates and closure.

## Draft outcomes

- A blueprint compiler can produce a bounded task DAG with path ownership and verification intent.
- A technology profile selects only reviewed framework kits before candidate work begins.
- Candidate execution, review, integration, escalation, and evaluation have explicit authorities.
- Research Workspace OS is the reference evaluation journey, not an implementation request.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** provider execution is not an available Wave-9 foundation until Wave-8 closes its returned LangGraph lane and deferred evaluation lane, and its integration authority records closure. The existing contracts define request, policy, event, usage, and result shapes; this draft does not assume dispatch, recovery, budget enforcement, cancellation propagation, or evidence retention operate reliably until that closure is demonstrated.

## Exclusions

No implementation, contract change, framework-kit addition, provider invocation, resource provisioning, application generation, or automatic merge is in scope for this draft.
