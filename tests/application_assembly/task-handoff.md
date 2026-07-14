# Wave-1 Task Handoff v1

Lane: assembly
Branch: feature/wave1-assembly
Base commit: 5606a0556a3bb822e0168e59c4de421ccb963860
Head commit: pending candidate commit
Worktree: ../servicefabric-wave1-assembly

## Objective

Implement application assembly only within the owned package and tests after the bootstrap commit.

## Changed Paths

- packages/servicefabric_application_assembly
- tests/application_assembly

## Candidate Commits

- pending

## Tests Executed

- python3 -m unittest discover -s tests/application_assembly -v
- git diff --check

Machine-readable evidence is stored in `codex/runs/wave-1/assembly/tests.json`.

## Contract Changes

none

## Deviations

The rendered prompt requires a handoff from the shared template, but the wave completion path policy only allows this lane to change `packages/servicefabric_application_assembly` and `tests/application_assembly`. The handoff is therefore committed under `tests/application_assembly/task-handoff.md`.

## Blockers

none

## Rollback

Revert the candidate commit for this lane.

## Next Action

Run wave task completion validation after the candidate commit is created.
