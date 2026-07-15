# Wave-4 Capability Registry Handoff

Lane: capability-registry
Branch: `agent/w4-capability-registry`
Base commit: `8852fd491870e153a70f9528a3e58d2c09841a05`
Registry candidate head: `df27a6625bf09f3d76e8d0c91d0265d63ac0761d`

## Candidate Commits

- `df27a6625bf09f3d76e8d0c91d0265d63ac0761d` — `fix(capability-registry): complete static capability registry`

## Changed Paths

- `packages/servicefabric_capability_registry/pyproject.toml`
- `packages/servicefabric_capability_registry/src/servicefabric_capability_registry/__init__.py`
- `packages/servicefabric_capability_registry/src/servicefabric_capability_registry/registry.py`
- `tests/capability_registry/__init__.py`
- `tests/capability_registry/test_registry.py`
- `docs/handoffs/wave-04/capability-registry.md`

## Tests Executed

- `PYTHONPATH=packages/servicefabric_capability_registry/src:/home/lorenzoccasoni/unibz/Thesis/Tool Builder/servicefabric-wave1-resources/packages/servicefabric_capability_model/src:packages/servicefabric_contracts/src /home/lorenzoccasoni/servicefabric-agent-state/wave-04/capability-registry/.venv/bin/python -m unittest discover -s tests/capability_registry -v` — passed, 8 tests.
- `python3 -m unittest discover -s tests/capability_model -v` — completed with 0 tests because this registry worktree intentionally contains no capability-model test files.
- `python3 -m unittest discover -s tests/operation_model -v` — could not run: the isolated registry worktree has no `tests/operation_model` directory.
- `git diff --check` — passed after the handoff edit.

The model and operation test directories are intentionally absent from this isolated registry lane after restoration to the Wave-4 bootstrap base. They must be run by integration after the model candidates are composed; no model or operation files were copied into this lane.

## Contracts Consumed

- `servicefabric_capability_model.CapabilityDefinition` is the only definition API consumed.
- Canonical serialization uses `CapabilityDefinition.model_dump(mode="json", by_alias=True)` and rehydrates with `CapabilityDefinition.model_validate`.
- The registry does not alter `EffectContract`, operation definitions, or any consumer projection.

## Decisions and Limitations

- One atomically replaced local JSON state file stores static definitions, SHA-256 content digests, and sorted application-to-capability indexes. This makes definition registration and index mutation one atomic replacement.
- Registration is process-serialized with a local advisory lock. Root, lock, and state-file symlinks are rejected; application IDs use the canonical bounded identifier form.
- This is static metadata storage only. It provides no availability, invocation, runtime, MCP, REST, CLI, or Python projection behavior.
- Cross-process locking uses POSIX `fcntl`; Windows support is intentionally outside the local Wave-4 scope.

## Integration Instructions

1. Integrate the accepted capability-model candidate before installing this package, so `servicefabric_capability_model` is available.
2. Install both package projects in the Wave-4 environment; no lockfile or CLI change is needed for this lane.
3. Compose authoring and CLI behavior in the integration lane by calling `register(definition, application_id)`, `list(application_id=None)`, and `describe(capability_id)`.
4. Run registry, capability-model, operation-model, and cross-lane acceptance tests from the integrated worktree.

## Blockers

None for the registry lane. Cross-lane model and operation tests require their candidate packages to be composed by integration.
