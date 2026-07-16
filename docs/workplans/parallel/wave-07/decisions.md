# Wave-7 Decisions

## Harness task-pack contract

- The accepted and integrated `CodexPromptHarness.prepare_task` result has exactly the keys `task_id`, `repository`, and `prompt`.
- `task_id` identifies the task, `repository` identifies its execution scope, and `prompt` contains the rendered instructions. These fields are sufficient for the Wave-7 evaluation journey.
- The earlier evaluation acceptance shape `task`, `instructions`, and `prompt` is obsolete and must not be enforced.
- Future evaluation prompts must instruct the evaluation lane to assert the authoritative `task_id`, `repository`, and `prompt` shape without requesting a harness implementation change.

