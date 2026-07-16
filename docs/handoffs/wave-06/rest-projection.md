# Wave-6 Task Handoff

Lane: `rest-projection`
Branch: `agent/w6-rest-projection`
Base commit: `3c6cdca08f4989d6932c3abe19df6539df4b3e50`
Candidate commits (apply in order):

1. `3d966a0cfedc717a348a9c70ee7268a9486f9292` — initial gateway implementation
2. `b49369976bc0cfa89366581c72cdc91e770462da` — source-layout correction
3. `fix(rest): delegate capability gateway through consumer facade` — returned-candidate correction

## Changed Paths

- `services/capability_rest_gateway/src/servicefabric_capability_rest_gateway/`
- `tests/capability_rest_gateway/test_gateway.py`
- `docs/handoffs/wave-06/rest-projection.md`

## Tests Executed

- `python3 -m unittest discover -s tests/capability_rest_gateway -v` — passed, 3 focused tests, executed with loopback-socket permission because the managed sandbox blocks all socket creation.
- `git diff --check` — passed.

## Contracts Consumed

- Integration-owned `servicefabric_client.capability_consumer.CapabilityConsumerFacade`, injected through the local `CapabilityConsumerBoundary` protocol.
- Only facade operations are consumed: `list_capabilities`, `describe_capability`, `capability_availability`, and `invoke_capability`.

## Decisions and Limitations

- The REST service neither imports nor accesses `CapabilityRegistry`, and it neither imports nor constructs `CapabilityRuntimeService`.
- The HTTP routes are exactly `GET /capabilities`, `GET /capabilities/{capability_id}`, `GET /capabilities/{capability_id}/availability`, and `POST /capabilities/{capability_id}/invoke`.
- Result records are projected into deterministic JSON field names and sorted JSON encoding. Known facade failures are bounded to 400, 404, or 409; unexpected failures return 500.
- The server binds only to literal IPv4 `127.0.0.1`. HTTP parsing and serving remain separate from canonical invocation, which is delegated unchanged through the facade.
- Authentication, TLS, remote binding, automatic route publication, and a production process launcher remain outside this lane.

## Blockers

- None.

## Rollback

- Revert the correction commit above to restore the returned candidate.
