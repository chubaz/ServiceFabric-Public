# Wave-1 Parallel Development

## Objective

Establish the first parallel development wave for application assembly, local resource bindings, framework kits and blueprints, adversarial regression review, and integration authority.

This document coordinates future work only. It does not implement application assembly, resource providers, blueprints, a development supervisor, or the capability system.

## Frozen Contracts

The base commit is `5606a0556a3bb822e0168e59c4de421ccb963860`.

AP-00C is already merged at that base. Treat the following as frozen unless the integration authority explicitly records approval:

```text
docs/contracts/application-module-v0.1.md
schemas/servicefabric/local/v1/**
packages/servicefabric_application_model/**
packages/servicefabric_process_runtime/**
packages/servicefabric_workspace/**
services/application_host/**
examples/text-utility/**
tests/ap_01a/**
tests/modules/**
tests/workspace/**
```

AP-00C already owns primitive application module contracts, FastAPI kit contract shape, managed-process lifecycle, health, ports, records, resources, and local workspace behavior.

## Package Ownership

`assembly` owns `packages/servicefabric_application_assembly/**` and `tests/application_assembly/**`.

`resources` owns `packages/servicefabric_resource_bindings/**` and `tests/resource_bindings/**`.

`kits-blueprints` owns `packages/servicefabric_framework_kits/**`, `packages/servicefabric_blueprints/**`, `tests/framework_kits/**`, `tests/blueprints/**`, and explicitly approved application fixtures.

`testing` owns `tests/adversarial/**`, approved architecture and AP-00C regression tests, and review documentation.

`integration` owns cross-lane acceptance, client CLI, Makefile, CI, dependency locks, development-supervisor integration, and shared contracts only when explicitly approved.

## Prohibited Overlap

Specialist agents must not modify shared CLI, CI, Makefile, dependency locks, common schemas, milestone state, or AP-00C frozen contracts.

Feature agents may create focused candidate commits after their own tests pass. They must not merge their branches.

Only the integration authority may accept candidate commits into the integration branch.

## Dependency Graph

```text
AP-00C frozen base
  -> testing regression review
  -> kits-blueprints
  -> resources
  -> assembly
  -> integration authority
```

Testing starts first to sharpen AP-00C regression coverage. Kits and resources may proceed independently after preflight. Assembly must consume published interfaces rather than reaching into implementation internals. Integration resolves cross-lane conflicts and accepts candidate commits.

## Integration Procedure

1. Bootstrap worktrees from the immutable base with `scripts/agent/bootstrap_wave_worktrees.py --wave wave-1`.
2. Launch one Codex session per lane using prompts rendered by `scripts/agent/render_wave_prompt.py`.
3. Require each feature lane to run preflight before editing.
4. Require each feature lane to create candidate commits only after its required tests pass.
5. Run completion checks against each candidate branch and the canonical committed handoff.
6. Integrate in the manifest order: testing, kits-blueprints, resources, assembly, integration.
7. The integration authority accepts, rejects, or returns candidate commits with a recorded reason.

## Commit-Candidate Procedure

Feature agents must:

1. Start on their assigned branch and worktree.
2. Run `python3 scripts/agent/wave_task_preflight.py --task TASK`.
3. Modify only allowed paths.
4. Run required tests and write a JSON test log under `codex/runs/wave-1/TASK/tests.json`.
5. Write a handoff from `docs/workplans/handoffs/wave-1/task-handoff-v1.md` to the lane's canonical `docs/handoffs/wave-01/<lane>.md` path.
6. Commit focused changes with the lane prefix policy.
7. Run `python3 scripts/agent/wave_task_completion.py --task TASK --test-log TEST_LOG`.
8. Stop without merging.

## Handoff Format

Use the versioned handoff template at `docs/workplans/handoffs/wave-1/task-handoff-v1.md`. The only committed authoritative handoff location is `docs/handoffs/wave-01/`. Runtime `.agent-runs/wave-01/<lane>/handoff.md` files are ignored mirrors generated from those canonical files.

Handoffs must record lane, branch, base, head, changed paths, tests executed, candidate commits, deviations, blockers, rollback, and next action.

## Failure And Escalation

Stop and escalate to the integration authority when:

```text
base commit does not match the manifest
working tree is dirty before preflight
required context files are missing
work touches forbidden paths
frozen contracts need changes
required tests cannot be run
candidate commits violate lane policy
another lane must change first
```

Do not repair violations by widening lane ownership locally. Record the blocker in the handoff and return the candidate for integration review.
