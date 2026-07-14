# Wave-2 Reference-App Handoff

Lane: reference-app
Branch: agent/w2-reference-app
Base commit: 0740ed11c267337a4d8194248a34ae6beda3832f
Head commit: correction commit recorded by this handoff
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
- correction commit: resolve all Research Notes module kits from the reviewed default catalogue

## Tests Executed

- python3 -m unittest discover -s tests/wave_02 -v
- python3 -m unittest discover -s tests/framework_kits -v
- python3 -m unittest discover -s tests/blueprints -v
- git diff --check

Machine-readable evidence: `.agent-runs/wave-02/reference-app/tests.json`.

## Contract Changes

none

## Deviations

- The local environment has no FastAPI installation, so process-level HTTP probing was not executed here. The API remains a standard FastAPI application and the focused suite verifies dependency-free persistence, manifest wiring, adversarial search behavior, and default-catalogue resolution for every module kit.

## Blockers

none

## Rollback

Revert the correction commit (and, if needed, the two earlier reference-app candidate commits) to restore the preceding manifest references.

## Next Action

Run the canonical supervisor journey with the injected `SF_DATABASE_PRIMARY_URL` binding.
