---
name: create-task
description: Author one Project Anton SWE task — prompt, frozen Harbor package, qualitative requirements, golden solution, Studio Task form and draft rubrics. Use when the user runs /create-task, or asks to create, design, write or scaffold a new Anton task or task prompt.
---

# create-task

Build one Anton task end to end.

## Run

Read [task-creation-prompt.md](../../../task-creation-prompt.md) in full and follow it
as the instructions for this turn. It owns the judgment, the process and the
deliverables; this skill adds only the session rules below.

If the user named a task type, repository or concept, use it and skip choosing one.
If they gave nothing, pick the concept yourself per the prompt's design question —
do not present a menu of alternatives.

## Session rules

- **Task ID.** If the user has a Studio Task ID, use it for `tasks/<task-id>/` and
  `[metadata].task_id`. Otherwise use a short kebab slug and tell the user it must be
  replaced with the Studio ID before submitting.
- **Author fields.** `author_name` / `author_email` are claims about the human. Ask,
  or leave `REPLACE` and say so — never fill them in on the user's behalf.
- **Proving the gate.** If Docker/Harbor is unavailable locally, run the verifier
  against the starting state, the golden solution, one valid alternative and one
  wrong fix with a local Python/pytest in the scratchpad, rewriting `/workspace` paths
  on a copy — never edit the shipped tests to make them runnable. Report which runs
  happened and which did not.
- **Never touch a frozen task.** If `tasks/<task-id>/trajectories/` already holds
  rollouts, stop and ask: any package change discards them.

## Verify, then stop

```bash
python3 tasks/gate.py tasks/<task-id>
```

Every BLOCK must PASS. Hand back exactly the prompt's deliverables, plus anything
unresolved. Do not run Studio rollouts or submit anything — those happen in the
Studio UI and are the user's to do.
