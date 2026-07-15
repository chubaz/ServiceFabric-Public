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
- `python3 -m unittest discover -s tests/wave_05 -v` — blocked before collection because the system Python lacks the locked `pydantic` dependency; the Wave-5 test environment is required.
- Focused Wave-5 environment command (`python -m unittest discover -s tests/wave_05 -v`) — reaches the real loopback HTTP journey but fails at `notes.create`; see blocker below.
- `git diff --check` — passed.

## Blocker

The composed CLI starts the Wave-3 generated `notes-api` (`servicefabric_client.wave3.Wave3ApplicationService`). Its `POST /notes` endpoint accepts a single `body` value and returns only `id` and `body`; the frozen Wave-5 operation declaration sends the valid canonical input `{ "title", "body" }` and requires a note output containing `id`, `title`, `body`, and `created_at`. FastAPI therefore returns HTTP 422 before a note can be created.

This is an implementation-composition mismatch outside the acceptance lane's allowed paths. The test intentionally remains a failing acceptance specification until the integration owner aligns the started Research Notes API with the registered Wave-5 operation and schemas. No implementation, CLI, Makefile, or shared metadata was changed here.

## Contracts Consumed

- Static capability registration remains distinct from runtime availability.
- Invocation validates the declared request schema before the reviewed HTTP adapter.
- Runtime availability derives from the owning `notes-api` module's health.
- Stop changes runtime availability only; it does not unregister static capability definitions.

## Rollback

Revert the acceptance-test commit and this handoff commit. No runtime state, implementation package, or shared contract was modified.
