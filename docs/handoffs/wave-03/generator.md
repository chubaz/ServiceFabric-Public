# Wave-3 Generator Handoff

## Lane

generator — deterministic blueprint materialization and local application creation.

## Candidate commits

`386f4f5` — `feat(generator): add atomic blueprint materialization`

## Scope and ownership check

Implemented only within `packages/servicefabric_application_generator`, `tests/application_generator`, and this handoff (plus the required `codex/runs/wave-03/generator/tests.json` evidence). No other lane was merged or modified.

## Frozen-contract compliance

The generator consumes the frozen `ApplicationBlueprint` and `ApplicationModule` model boundaries. It validates generated manifests with `load_module_definition_from_dict` and `validate_module_graph`; it does not modify the application model, workspace service, CLI, or runtime.

## Tests and exact results

- Focused generator suite: 3 tests passed with the new package and frozen dependencies on `PYTHONPATH`.
- `git diff --check`: passed.
- `python3 -m compileall -q packages/servicefabric_application_generator tests/application_generator`: passed.
- The literal required unittest command was also attempted; this checkout does not install the new package into the interpreter, so it reports `ModuleNotFoundError`. Evidence is recorded in `codex/runs/wave-03/generator/tests.json`.

## Known limitations

The generator publishes application files and ordinary FastAPI-compatible starter source, but workspace registry integration and lifecycle/build orchestration belong to the application-builder and integration lanes. YAML files are emitted as deterministic JSON, which is valid YAML and avoids serializer ordering drift.

## Integration notes

The application-builder lane can consume `GenerationResult.files` and the generated `.servicefabric` manifests. The target is never overwritten; generation stages in a hidden sibling directory and removes that staging directory on failure.

## Recommendation

Accept as a focused candidate after reviewing the commit hash below; integration should apply it in the declared Wave-3 order without merging another specialist lane here.
