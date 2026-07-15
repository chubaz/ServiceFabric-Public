# Wave-4 Task Handoff

Lane: capability-registry
Branch: agent/w4-capability-authoring (shared checkout; rendered lane expects agent/w4-capability-registry)
Base commit: 162bc3d64e8c2a9d044895f8c57b650f1cddb22f
Candidate commit: 4eaab5a

## Changed Paths

- `packages/servicefabric_capability_registry/`: new dependency-free package exposing `CapabilityRegistry` and registry errors.
- `tests/capability_registry/`: focused tests for atomic persistence, canonical digest, idempotency, conflicts, deterministic listing, indexing, and path safety.

## Tests Executed

- `python3 scripts/agent/wave_task_preflight.py --wave wave-04 --task capability-registry --format json` — blocked only by the shared checkout branch name.
- `PYTHONPATH=packages/servicefabric_capability_registry python3 -m unittest discover -s tests/capability_registry -v` — passed (5 tests).
- `make verify-wave-04` — passed.
- `make verify-current` — passed.
- `git diff --check` — passed.

## Contract Changes

None. The registry accepts validated static definitions, serializes them canonically, and stores only static definition data. It adds no invocation, runtime availability, MCP, REST, Python, or route-inference behavior.

## Decisions and Limitations

- Capability records use SHA-256 keyed filenames, integrity envelopes, exclusive lock files, fsync-backed temporary writes, and deterministic JSON ordering.
- Re-registering byte-equivalent canonical content returns the same digest; a different payload for the same capability identifier raises `CapabilityConflictError` without replacing the record.
- Application indexes are maintained as deterministic sorted capability-id lists and are updated under their own exclusive lock.
- The package is intentionally dependency-free so it can compose with the capability-model lane when integrated.

## Blockers

The lane preflight could not pass because this checkout is on `agent/w4-capability-authoring`; no frozen contract or cross-lane change was required.
