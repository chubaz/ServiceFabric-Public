# Wave-5 Acceptance Handoff

Lane: `acceptance`  
Branch: `agent/w5-acceptance`  
Base commit: `53f53ca8a4a9a47887902b84a91bc27a812e9483`

## Changed Paths

- `tests/wave_05/test_research_notes_acceptance.py`
- `docs/handoffs/wave-05/acceptance.md`

## Acceptance Coverage

One end-to-end CLI journey creates and registers Research Notes, starts its development application, and asserts:

- exactly `notes.create`, `notes.get`, and `notes.search` are statically registered;
- all three are available while Research Notes is healthy;
- `notes.create` succeeds through the reviewed loopback HTTP adapter and `notes.search` returns that exact created note;
- invalid create input raises `SchemaValidationError` without an additional HTTP-adapter call;
- stopping the application makes all three capabilities unavailable while `capabilities list` still returns the three static definitions.

## Tests Executed

- `make agent-preflight` — passed.
- `source .agent-runtime.env && python3 -m unittest discover -s tests/wave_05 -v` — passed (one test).
- `git diff --check` — passed.

## Runtime Bootstrap Limitation

The acceptance runtime initializer installs the contracts lock and local editable packages, but not the Research Notes API runtime dependencies. Before the passing run, the disposable acceptance virtualenv was provisioned from `5_core_services/fastapi_base/requirements/runtime.lock`, supplying the reviewed FastAPI and Uvicorn dependencies. This altered only disposable agent state; no repository dependency metadata changed.

## Contracts Consumed

- Static capability registration remains distinct from runtime availability.
- Invocation validates the declared request schema before the reviewed HTTP adapter.
- Runtime availability derives from the owning `notes-api` module's health.
- Stop changes runtime availability only; it does not unregister static capability definitions.

## Rollback

Revert the acceptance-test commit and this handoff commit. No implementation package or shared contract was modified.
