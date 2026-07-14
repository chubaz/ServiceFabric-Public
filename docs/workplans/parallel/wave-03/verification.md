# Wave-3 Verification

The focused gate must cover generator, builder, guidance, acceptance, application assembly, resource bindings, framework kits, blueprints, supervisor/process runtime, workspace, Wave-2 regressions, dependency locks, compilation, `python3 -m pip check`, and `git diff --check`.

The fresh-workspace journey is:

```text
workspace init -> apps create -> apps modules -> apps validate -> dev prepare -> dev start -> dev status -> dev restart -> apps build -> dev stop
```

Tests must assert deterministic generated files, safe collision handling and rollback, ordinary generated source, validation, lifecycle preservation, build manifests, and cleanup. `make verify-wave-03` is the canonical integration gate.
