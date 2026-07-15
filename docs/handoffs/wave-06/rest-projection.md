# Wave-6 Task Handoff

Lane: `rest-projection`
Branch: `agent/w6-rest-projection`
Base commit: `9b40277fc648e1673a98d32f49ed2d444d632dd3`
Candidate commit: `3d966a0cfedc717a348a9c70ee7268a9486f9292`

## Changed Paths

- `services/capability_rest_gateway/servicefabric_capability_rest_gateway/`
- `tests/capability_rest_gateway/test_gateway.py`
- `docs/handoffs/wave-06/rest-projection.md`

## Tests Executed

- `python3 -m unittest discover -s tests/capability_rest_gateway -v` — passed, 3 tests. The managed sandbox denied loopback socket creation; the identical suite passed with Python 3.11.2 outside that socket restriction.
- `git diff --check` — passed.

## Contracts Consumed

- The composed Wave-5 capability boundary's public `list_capabilities`, `describe_capability`, `availability`, and `invoke` operations.
- Registered capability definitions and derived availability and invocation results are projected as JSON values without changing their owners or contracts.

## Decisions and Limitations

- The server binds only to IPv4 `127.0.0.1`; other bind addresses are rejected before socket creation.
- Routes are limited to discovery, description, availability, and invocation under `/v1/capabilities`.
- Invocation accepts only a bounded JSON object containing exactly `input`; the projection delegates the value unchanged and contains no invocation or application-endpoint logic.
- Authentication, remote binding, TLS, automatic route publication, and a production process launcher remain outside this specialist lane.

## Blockers

- None.

## Rollback

- Revert candidate `3d966a0cfedc717a348a9c70ee7268a9486f9292` and the subsequent handoff-only commit.
