# AP-00C Regression Review

Lane: testing
Wave: wave-1
Base commit: 5606a0556a3bb822e0168e59c4de421ccb963860

## Scope

Reviewed AP-00C frozen behavior for managed local hosting, process identity, port binding, runtime records, resource observations, and architecture boundaries. This review adds tests only; no frozen implementation, contract, schema, package, service, CLI, Makefile, or CI path was changed.

## Added Coverage

- Adversarial process-runtime tests under `tests/adversarial` for stale PID records, malformed runtime records, interrupted atomic-write fragments, exact command ownership, and loopback-only port allocation.
- Architecture regression tests under `tests/architecture` ensuring `servicefabric_process_runtime` remains framework-neutral, does not depend on Wave-1 feature-lane packages, has no dynamic code execution escape hatches, and keeps process status separate from resource measurements.

## Findings

- AP-00C host integrity coverage was already strong for CLI-level lifecycle, artifact integrity, authorization denial, and malformed host state.
- Lower-level process-runtime regressions were underrepresented before this lane because `tests/adversarial` did not exist.
- No frozen contract change was required.

## Limitations

- The new tests intentionally avoid asserting implementation details outside the AP-00C runtime boundaries.
- The adversarial tests run without starting real application servers; existing `tests/ap_01a` remains the hosted vertical-slice coverage.

## Rollback

Revert the testing-lane candidate commit to remove the new adversarial tests, architecture regression, review note, evidence log, and handoff.
