# Wave-2 Integration Order

1. Freeze contracts and record the base.
2. Review candidates at midday.
3. Integrate runtime bindings, kit execution, reference application, then supervisor.
4. Run end-of-day cross-package acceptance and record accept, reject, or revision decisions.

Immediate integration is reserved for a shared blocker or an approved contract correction. Only the integration authority accepts candidates.

Initialize each lane with the positional runtime interface. For integration:

```bash
scripts/agents/init_worktree_runtime.sh integration "$SF_WT_INTEGRATION" "$SF_STATE_BASE" wave-02
```

Use the equivalent lane, worktree variable, and `wave-02` for specialists. Bootstrap through:

```bash
scripts/agents/finalize_existing_worktrees.sh --wave wave-02 --bootstrap-sha SHA --dry-run
scripts/agents/finalize_existing_worktrees.sh --wave wave-02 --bootstrap-sha SHA
```

`SHA` is the committed Wave-2 harness head, not the original Wave-2 base. The finalizer first verifies the integration worktree equals that SHA, then fast-forwards each clean specialist branch to it.
