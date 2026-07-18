# Wave-10 task handoff

- Task: Evidence — deterministic manifest-bounded application evidence collection.
- Candidate commit: `2b8f64b` (`feat(evidence): collect manifest-bounded application evidence`).
- Exact approved base: `5d0add1332d71e79fc138aad42c025a3607d8aef`.
- Owned-path diff: Adds `servicefabric_application_evidence` and its focused tests; updates this handoff only.
- Validation: `python3 -m unittest discover -s tests/application_evidence -v` via the Wave-10 isolated environment (3 tests passed); `git diff --check` passed.
- Evidence and decisions: Collection accepts supplied manifest content and authoritative Wave-9 plan/handoff records only. It never resolves references, reads repository paths, discovers files, or copies provider state. It rejects unknown task results and changed paths outside both the manifest declaration and the task's allowed paths; outputs and SHA-256 digests are sorted deterministically.
- Blockers or limitations: The branch contains the two Wave-10 bootstrap commits after the declared base; the declared base is an ancestor. No frozen contract changes were needed.
- Rollback: Revert the focused candidate commit; no persistent state or external system is changed.
