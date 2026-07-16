# Frozen contracts

`packages/servicefabric_agentic_contracts` is the Wave-7 public contract seed. Specialists consume it and do not alter it.

The following boundaries are frozen for Wave 7:

1. Agentic contracts contain data and protocols only.
2. Context building does not plan.
3. Planning does not persist or execute.
4. Run storage does not schedule.
5. Orchestration does not invoke models or edit files.
6. Harnesses execute task contracts but do not plan.
7. Agent tools use public ServiceFabric boundaries only.
8. Capability access delegates through `CapabilityConsumerFacade`.
9. No arbitrary shell tool exists.
10. Pi, LangGraph, and provider adapters remain owned by Wave 8.

`contractsStatus: frozen` is the required state before any specialist work begins.
