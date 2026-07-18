# Wave-9 candidate-review standalone handoff

- Approved base: `3bf95f971aa73ca5105e14e90e04e4a16511a0b0`
- Standalone implementation: `66136e680270e620f278c9960c6291d8a2318eee`
- Superseded candidate: `fa33c0b2216d559bbff8234ee2300002ff8a361f`
- Backup branch: `backup/w9-candidate-review-pre-recovery-fa33c0b`
- Owned paths: `packages/servicefabric_application_candidate_review/**`, `tests/application_candidate_review/**`

## Validation

- Focused suite: 6 passed.
- `python3 -m compileall -q packages/servicefabric_application_candidate_review/src` — passed.
- `git diff --check` — passed.

The service accepts only a canonical full immutable commit SHA, resolves it as a
commit object, preserves that exact SHA in `CandidateReviewDecision`, and
performs read-only review only.

## Integration instruction

Integrate only `66136e680270e620f278c9960c6291d8a2318eee`, then this handoff.
Do not integrate `fa33c0b`.
