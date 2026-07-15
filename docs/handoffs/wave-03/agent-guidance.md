# Wave-3 Lane Handoff

## Lane

`agent-guidance`

## Candidate commits

- `2ad5fcb feat(guidance): compose reviewed application guidance`

## Scope and ownership check

Changed only the assigned guidance package and focused tests. The package composes
deterministic root and per-module `AGENTS.md` files; it performs no filesystem
writes and has no coding-assistant runtime dependency.

## Frozen-contract compliance

No frozen contract or shared boundary changed. The public guidance-fragment
composition surface is local to `servicefabric_agent_guidance` and accepts only
reviewed built-in kit fragments.

## Tests and exact results

- `PYTHONPATH=packages/servicefabric_agent_guidance python3 -m unittest discover -s tests/agent_guidance -v` — passed: 4 tests, `OK`.
- `PYTHONPATH=packages/servicefabric_agent_guidance python3 -m compileall -q packages/servicefabric_agent_guidance` — passed.
- `git diff --check` — passed.

Test evidence is recorded in `codex/runs/wave-03/agent-guidance/tests.json`.

## Known limitations

The package intentionally does not materialize files; generator integration must
write the returned `GuidanceBundle.files` using its established safe-write path.
Only FastAPI service, React web, Python worker, and Python library reviewed
fragments are included in this Wave-3 scope.

## Integration notes

Call `compose_guidance({module_id: kit_reference, ...})`; write each returned
relative path and text exactly as supplied. Unknown kit references fail closed
with `UnknownGuidanceKit`.

## Recommendation

Cherry-pick `2ad5fcb` during Wave-3 integration, then connect the generator's
materialization step to `compose_guidance` without changing frozen contracts.
