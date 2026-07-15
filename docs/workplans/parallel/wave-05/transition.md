# Wave-5 Transition

Bootstrap is ready when both Wave-5 manifests select the frozen base and integration branch, all five lane manifests and canonical handoffs exist, readiness and queue state agree, prompts render for every lane, and task preflight passes on each clean matching branch.

Specialist work begins from the bootstrap commit. Completion remains pending until all four candidate lanes are explicitly accepted and integrated, `make verify-wave-05` passes, `make verify-current` passes once at final closure, and readiness plus queue records are moved to complete.
