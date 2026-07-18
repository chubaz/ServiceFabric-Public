# Wave-10 task handoff

- Task: Generate deterministic, manifest-bounded `CapabilityCandidate` records from explicit operation and capability declarations.
- Candidate commit: This focused candidate commit; integration should record its immutable SHA during review.
- Exact approved base: `5d0add1332d71e79fc138aad42c025a3607d8aef`
- Owned-path diff: Added `servicefabric_capability_distillation`, its focused tests, and this handoff only.
- Validation: `/home/lorenzoccasoni/servicefabric-agent-state/wave-10/capability-distillation/.venv/bin/python3 -m unittest discover -s tests/capability_distillation -v` (4 passed); `git diff --check` passed.
- Evidence and decisions: Candidates require declared operations named in `ApplicationEvidenceBundle`, optionally require explicit declared capability references, and accept only bundle-named evidence references. All records have status `proposed`; this lane neither approves nor publishes.
- Blockers or limitations: The system `python3` lacks Pydantic, so focused tests used the rendered lane virtual environment. No frozen contracts changed.
- Rollback: Revert the focused candidate commit; no registry, application, or persistent runtime state was modified.
