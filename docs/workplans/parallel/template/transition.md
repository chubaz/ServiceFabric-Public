# Standard Wave Transition

1. Close the current wave with `scripts/agents/close_wave.sh --wave WAVE_ID`.
2. Create and merge the pull request manually.
3. Fetch `origin/main` and select the merged commit as the next base.
4. Start the next wave with `scripts/agents/start_next_wave.sh --wave NEXT_WAVE --base origin/main`.
5. Launch the integration lane.
6. Freeze contracts with `scripts/agents/record_contracts_frozen.sh --wave NEXT_WAVE`.
7. Launch specialist lanes only after the freeze succeeds.

Neither transition script resets, force-pushes, deletes branches or worktrees, or merges a pull request.
