# Wave-2 Reference-App Handoff

Lane: reference-app
Branch: agent/w2-reference-app
Base commit: 715de644eff2ee003469f14d574c4b70706bc70a
Head commit: 679d72ad7b8b4959f9eeb721f6ac12fe63f9825b
Worktree: SF_WT_REFERENCE_APP

## Objective

Implemented the ordinary modular Research Notes source: a public Python domain library, a FastAPI API backed by an injected SQLite URL, and a standard static browser frontend. Added persistence, manifest, and adversarial acceptance fixtures without changing framework or supervisor packages.

## Changed Paths

- examples/research-notes/application.yaml
- examples/research-notes/domain/**
- examples/research-notes/api/**
- examples/research-notes/web/**
- tests/wave_02/test_research_notes_application.py
- docs/handoffs/wave-02/reference-app.md

## Candidate Commits

- 45f9735 feat(research-notes): add modular notes application
- 679d72a test(research-notes): add persistence acceptance fixtures

## Tests Executed

- python3 -m unittest discover -s tests/wave_02 -v
- git diff --check

Machine-readable evidence: `.agent-runs/wave-02/reference-app/tests.json`.

## Contract Changes

none

## Deviations

- The local environment has no FastAPI installation, so process-level HTTP probing was not executed here. The API remains a standard FastAPI application and the focused suite verifies the dependency-free domain persistence, manifest wiring, and adversarial search behavior.

## Blockers

none

## Rollback

Revert candidate commits `45f9735` and `679d72a` (and this handoff commit) to remove the reference application and its fixtures.

## Next Action

Integrate with the Wave-2 framework-kit, runtime-binding, and supervisor lanes; run the canonical supervisor journey with the injected `SF_DATABASE_PRIMARY_URL` binding.
