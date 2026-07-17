# Transition from Wave 8

Wave-9 draft work consumes the Wave-7 agentic contracts and Wave-8 provider contracts as frozen planning inputs. It does not reopen or extend either contract.

Wave-8 readiness currently records integrated provider-runtime, Pi, Codex, Claude, and Gemini lanes, but a returned LangGraph lane and deferred evaluation lane. Consequently, Wave-9 must not treat provider orchestration or evaluation behavior as closed.

Transition gate for any future Wave-9 implementation:

1. Wave-8 integration authority accepts the LangGraph revision and launches/accepts evaluation, or formally records an alternative closure decision.
2. Wave-8 closure demonstrates the applicable verification gates and records final integration status.
3. A separately approved Wave-9 implementation workplan defines owned paths, contracts, verification, rollback, and integration authority.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** this transition gate is satisfied before any factory invokes a provider, relies on provider scheduling/recovery, or uses provider-derived evidence to accept application work. Until then, this directory and its manifests are draft-only planning material.
