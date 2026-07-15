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

No specialist-owned functionality was implemented or modified. All four specialist branches contain only bootstrap commit `b3bcacc`; no candidate is available for review or composition. `make verify-current` is deferred: the Wave-5 verification policy permits it once only at final closure.

## Blockers

Await focused candidate commits and handoffs from availability, HTTP-adapter, invocation, and acceptance lanes. The final Wave-5 gate cannot run until their owned test directories and packages exist.

## Rollback

Revert this handoff-only integration record; no runtime, registry, contract, or projection behavior changed.
