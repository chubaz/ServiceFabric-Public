# Wave-5 Verification

Specialists run only their focused suite and `git diff --check`. The focused-test ceilings are four for availability, four for invocation, three for the HTTP adapter, and two for acceptance.

`make verify-wave-05` runs only:

- `tests/capability_runtime`;
- `tests/capability_invocation`;
- `tests/http_operation_adapter`;
- `tests/wave_05`;
- one Wave-4 capability CLI smoke test;
- one AP-00C process-runtime smoke test;
- dependency-lock verification;
- `pip check`;
- `compileall` for the changed Wave-5 packages;
- `git diff --check`.

It must not invoke `verify-wave-01`, `verify-wave-02`, `verify-wave-03`, or `verify-wave-04`. Run `make verify-current` once, only at final closure.
