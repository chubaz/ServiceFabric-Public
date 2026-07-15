# Wave-4 Capability Registry Handoff

Lane: capability-registry
Branch: `agent/w4-capability-registry`
Wave-4 base SHA: `162bc3d64e8c2a9d044895f8c57b650f1cddb22f`
Specialist bootstrap/base SHA: `8852fd491870e153a70f9528a3e58d2c09841a05`
Implementation candidate head: `94d34c4402fe81ff2edb9c78c12cc2b17b726b69`

## Candidate Commits

- `df27a6625bf09f3d76e8d0c91d0265d63ac0761d` — static registry implementation.
- `3866227a9b3f4363654e86790391e76af83e5686` — prior handoff report.
- `94d34c4402fe81ff2edb9c78c12cc2b17b726b69` — scope audit, dangling-symlink hardening, and focused safety coverage.

## Changed Paths

- `packages/servicefabric_capability_registry/pyproject.toml`
- `packages/servicefabric_capability_registry/src/servicefabric_capability_registry/__init__.py`
- `packages/servicefabric_capability_registry/src/servicefabric_capability_registry/registry.py`
- `tests/capability_registry/__init__.py`
- `tests/capability_registry/test_registry.py`
- `docs/handoffs/wave-04/capability-registry.md`

The complete candidate diff from the specialist bootstrap was audited. Every changed path is lane-owned; no out-of-scope path required restoration.

## Contracts Consumed

- `servicefabric_capability_model.CapabilityDefinition` only.
- `model_dump(mode="json", by_alias=True)` for canonical persisted content and `model_validate` for rehydration.
- The frozen `EffectContract` is consumed only as part of the definition; no frozen contract is modified.

## Tests and Results

- `PYTHONPATH=packages/servicefabric_capability_registry/src:/home/lorenzoccasoni/unibz/Thesis/Tool Builder/servicefabric-wave1-resources/packages/servicefabric_capability_model/src:packages/servicefabric_contracts/src /home/lorenzoccasoni/servicefabric-agent-state/wave-04/capability-registry/.venv/bin/python -m unittest discover -s tests/capability_registry -v` — passed, 11 tests.
- `python3 -m unittest discover -s tests/capability_registry -v` — blocked: this isolated branch does not contain or install the separately owned `servicefabric_capability_model` package (`ModuleNotFoundError`).
- `python3 -m unittest discover -s tests/capability_model -v` — passed with 0 discovered tests because that separately owned directory is absent from this branch.
- `git diff --check` — passed.
- `python3 scripts/agent/wave_task_preflight.py --wave wave-04 --task capability-registry --format json` — passed.
- `python3 scripts/agent/wave_task_completion.py --wave wave-04 --task capability-registry --test-log .agent-runs/wave-04/capability-registry/tests.json --format json` — checker could not complete because the committed Wave-4 task manifest has no `candidate_commit_policy`, which the checker unconditionally reads. This is an integration-owned manifest/checker defect; no lane-owned file can correct it.

Registry coverage includes first registration, identical idempotency, conflicting identity reuse, deterministic ordering, describe, application indexing/filtering, malformed records, atomic write-failure recovery, traversal rejection, and root/state/lock symlink rejection.

## Limitations

- Static declarations only: no runtime availability, invocation, MCP, REST, CLI, Python projection, blueprint generation, or capability authoring.
- Persistence is one local JSON state file with SHA-256 content digests and sorted reciprocal application indexes.
- Registration uses a POSIX `fcntl` advisory lock; Windows locking is out of scope.

## Integration Instructions

1. Compose the accepted capability-model package before installing the registry package.
2. Install both packages in the Wave-4 test environment; no lockfile, CLI, or consumer change belongs to this lane.
3. Use only `register(definition, application_id)`, `list(application_id=None)`, and `describe(capability_id)` from integration-owned adapters.
4. Run the recorded focused commands and Wave-4 integration acceptance tests after composition.

## Blockers

The isolated registry branch does not contain the separately owned capability-model package or tests. The plain registry command therefore requires the composed Wave-4 environment (or the configured registry test environment); no cross-lane files were copied here. The lane completion checker additionally has a manifest/schema mismatch (`candidate_commit_policy` is missing) that integration must repair before accepting a passing completion result.
