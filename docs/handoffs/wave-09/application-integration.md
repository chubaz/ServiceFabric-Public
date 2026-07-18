# Wave-9 application-integration standalone handoff

- Approved base: `3bf95f971aa73ca5105e14e90e04e4a16511a0b0`
- Standalone implementation: `f755ecf0b550e72c8eb84a737ae643dfaccd22bf`
- Superseded implementation: `6076a55d73db97102ee1c1c9232d765582cd845f`
- Superseded handoff: `f9c3efecc1ea700aebb8835837d8fddcc08143d3`
- Backup reference: preserved outside integration history
- Owned paths: `packages/servicefabric_application_integration/**`, `tests/application_integration/**`

## Validation

- Focused suite: 5 passed.
- `python3 -m compileall -q packages/servicefabric_application_integration/src` — passed.
- `git diff --check` — passed.

The service requires a clean expected branch/head, accepted exact non-superseded
candidate SHA, reviewed changed paths, declared verification, and exact apply.

## Integration instruction

Integrate only `f755ecf0b550e72c8eb84a737ae643dfaccd22bf`, then this handoff.
Do not integrate `6076a55d73db97102ee1c1c9232d765582cd845f` or `f9c3efecc1ea700aebb8835837d8fddcc08143d3`.
