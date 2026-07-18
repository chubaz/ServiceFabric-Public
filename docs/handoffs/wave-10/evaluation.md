# Wave-10 evaluation handoff

- Task: Complete one black-box distillation journey from a synthetic completed Wave-9 factory run and generated application.
- Candidate commit subject: `test(wave-10): complete distillation journey`.
- Exact base: `ff398ff863b70793c0440f81157217546344a5ee`.
- Owned paths: `tests/wave_10/test_distillation_journey.py`; `tests/fixtures/wave_10/reviewed_distillation_journey.json`; `docs/handoffs/wave-10/evaluation.md`.

## Evidence

The single test materializes durable Wave-9 plan, result, lifecycle, unmet-requirement, and integrated-handoff records, plus a generated application containing an undeclared trap file. It then uses the public `ApplicationFactoryService` projection and `DistillationService` composition with the real decision store, capability registry, technique-policy catalog, and engineering-pattern catalog.

- Two collections read the one exact declared manifest, emit only the declared manifest/reference sets and two reported changed paths, exclude the undeclared marker, and compare equal.
- Analysis compares equal across runs and yields exactly one `CapabilityCandidate`, `TechniquePolicyCandidate`, `EngineeringPatternCandidate`, `BlueprintEvolutionProposal`, and `SystemChangeProposal`. The capability registry is empty before analysis; the approved profile, successful results, repeated verification command, and three-lane topology are asserted.
- Capability, technique policy, and engineering pattern are approved. Blueprint evolution is rejected and system change is undecided. Two reports and persisted catalog snapshots compare equal; the three approved records publish once, while both proposal references remain unpublished and unapplied.
- Generated-application and ServiceFabric source digests compare before and after. `ProviderRuntime.execute` is guarded and asserted unused.
- `servicefabric doctor --json` returns exactly 12 named checks with a bounded key set and payload size. Its exit code is asserted to match the transparent `ok` field.

## Validation

- Focused journey: passed, 1 test.
- `make verify-current`: passed for `ap-00-modular-framework-kits/readiness`.
- `git diff --check`: passed.
- `make verify-wave-10`: the new journey and preceding Wave-10 suites pass; the aggregate target later fails on its existing stale selector `tests.release_readiness.test_doctor.ReleaseDoctorTests`, while the module defines `DoctorTests`. The Makefile is outside this task's allowed paths.

## Limitations and rollback

The current Wave-10 path configuration points at `packages/servicefabric_release_readiness/src`, although that package is rooted directly under `packages/servicefabric_release_readiness`; doctor exposes that package-import failure in its report instead of hiding it. No provider, generated source, blueprint, proposal, or ServiceFabric source is modified; only temporary reviewed publication catalogs are written during the test.

Rollback by reverting the single candidate commit. No persistent runtime data or migration is involved.
