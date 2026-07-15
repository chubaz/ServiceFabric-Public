# Wave-5 Integration Handoff

Lane: `integration`
Branch: `integration/phase2-wave5`
Base commit: `53f53ca8a4a9a47887902b84a91bc27a812e9483`
Candidate commit: none

## Changed Paths

- `docs/handoffs/wave-05/integration.md`

## Tests Executed

- `python3 scripts/agent/wave_task_preflight.py --wave wave-05 --task integration` — passed.
- Wave-5 bootstrap coverage from `tests/agent` — passed (five tests).
- `make verify-wave-05` — blocked before specialist candidates exist: `tests/capability_runtime` is not yet present.
- `git diff --check` — passed before this handoff update.

The full `tests/agent` discovery also has one environment-dependent failure: its fresh-runtime test cannot download locked `annotated-types==0.7.0` because network resolution is unavailable. This is unrelated to Wave-5 contracts.

## Contracts Consumed

- `contractsStatus: frozen` is recorded in `config/agent/waves/wave-05/readiness.json` and remains in force.
- Static `CapabilityRegistry` definitions remain unchanged; availability is runtime-only and derives from owning-module health.
- Invocation composes independently with the reviewed HTTP transport; schemas validate before and after transport.
- Only healthy owning modules are available; HTTP invocation is loopback-only.
- MCP, REST gateway, Python SDK, and agent projections remain excluded.
- Lane manifests have disjoint owned paths and preserve the specialist focused-test ceilings.

## Decisions and Limitations

No specialist-owned functionality was implemented by the integration lane. `make verify-current` remains deferred: the Wave-5 verification policy permits it once only at final closure.

## First implementation candidate review

Accepted and merged, after complete candidate-diff review, ownership/frozen-contract checks, and focused verification:

- Availability — candidate `371804cfada9873d3050c9948f382114c0b2e031`; integrated by `ee9a7dc47c3fa5e532a2a801e95b2734a62238f0`. Its three focused tests passed. The derived availability view remains separate from static registration and only reports availability for a running, healthy owning module.
- HTTP adapter — candidate `419e1a752a4ddf60efd164c201d0961cad15d1bd`; integrated by `ef1762ed54e3768d5d323394b0c52a8bf403c614`. Its three focused tests passed. It is transport-only, enforces reviewed JSON bindings and literal loopback endpoints, and does not perform invocation or projection work.
- Invocation — candidate `8c6cebe7074e9ec45bc2686778a3ea9c91aa973e`; integrated by `dc939078043c095996a6a36b23959c41f9e6ff94`. Its four focused tests passed. It resolves reviewed definitions, rejects unavailable capabilities before transport, and validates schemas before and after the transport call.

Each candidate modified only its declared lane paths plus its canonical handoff. No frozen contract path changed. The acceptance lane was not reviewed or merged, and final completion integration was not performed.

## Blockers

The acceptance candidate `a0f9c12d55a88e61d5c7aea18cb187d3f20b35ea` was returned. Its complete delta is confined to `tests/wave_05/test_research_notes_acceptance.py` and its canonical handoff, and it invokes no redundant full-wave suite. Its single focused test fails before acceptance assertions because `apps dev start research-notes` routes through the Wave-3 development service and its process health check times out. The candidate is not merged; Wave-5 final verification is deferred until this integration-owned runtime composition issue is remediated and the acceptance test passes.

## Rollback

Revert this handoff-only integration record; no runtime, registry, contract, or projection behavior changed.
