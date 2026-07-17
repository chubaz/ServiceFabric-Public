# Wave-08 Codex lane handoff

## Lane

- `codex`

## Candidate commits

- `b7b40e6 feat(codex): add provider adapter`

## Scope and ownership check

- Added only `packages/servicefabric_codex_adapter` and `tests/codex_adapter`.
- This handoff is the sole documentation change in the lane-owned handoff path.

## Frozen-contract compliance

- `CodexAdapter` uses only `servicefabric_agent_provider_contracts` request,
  event, handle, usage, and result contracts.
- It constructs argv and translates JSONL records only; the shared runtime owns
  all subprocess lifecycle behavior.

## Tests and exact results

- `source .agent-runtime.env && python3 -m unittest discover -s tests/codex_adapter -v`
  passed: 3 tests.
- Evidence is recorded in `.agent-runs/wave-08/codex/tests.json`.

## Known limitations

- The adapter intentionally does not probe or invoke the Codex executable.
- It reports process outcomes through the shared contracts; no task-result
  extraction is inferred from provider event payloads.

## Integration notes

- Register `CodexAdapter` with the shared provider runtime when composing the
  Wave-08 provider inventory.

## Recommendation

- Accept `b7b40e6` as the Codex adapter candidate. Rollback is a revert of that
  commit; no persistent state or migrations are involved.
