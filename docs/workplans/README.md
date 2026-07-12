# Repository Workplans

`AGENTS.md` holds stable rules; milestone files hold changing scope. `current.md` points to the single current milestone configured in `config/agent/milestones.json`. Compact resumable state lives in `status.json` and is updated with `update_status.py`. Verification commands are committed command arrays. Completed plans move to `archive/`; `prepare_handoff.py` writes a local `.agent/handoff.md`.
