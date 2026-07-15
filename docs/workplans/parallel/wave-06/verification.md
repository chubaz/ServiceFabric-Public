# Wave-6 Verification

Specialists run their focused suite and `git diff --check`; each projection lane has a three-test maximum. Acceptance has one end-to-end journey and must not start before composition.

`make verify-wave-06` runs only the three projection suites, the one Wave-6 acceptance suite, one Wave-5 invocation smoke test, one existing MCP projection smoke test, dependency-lock verification, `pip check`, `compileall` for changed Wave-6 paths, and `git diff --check`. It does not recursively run prior wave gates. `make verify-current` runs once at final closure.
