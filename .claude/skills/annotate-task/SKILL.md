---
name: annotate-task
description: Annotate a Project Anton A/B trajectory pair — check pair eligibility, score Dimension 0 and the eight dimensions, answer the prompt-specific rubrics, pick the pairwise preference, and write annotation.json. Use when the user runs /annotate-task, or asks to score, evaluate, compare or annotate trajectories A and B for an Anton task.
---

# annotate-task

Annotate one frozen Anton task's A/B pair.

## Run

Read [annotation-prompt.md](../../../annotation-prompt.md) in full and follow it as the
instructions for this turn. It owns the order of work, the judging rules and the
deliverables.

## Inputs

Expect `tasks/<task-id>/` with `harbor/` and `trajectories/a.json`, `b.json`. If the
trajectories are missing, ask the user to export them from Studio (Trajectory A / B
panel: prompt, final answer, diff, logs) — do not annotate from a summary. `04`:
"Informal summary without the actual trajectory" is not acceptable.

If there is no Harbor package locally, work from what the user pastes, but say that
the gate's package checks were skipped.

## Session rules

- **Evidence or nothing.** Every score and rubric answer cites a step, `file:line`,
  test or hunk that you actually read in this session. If a trajectory is truncated
  and the deciding evidence is not visible, say so in the reason and flag it —
  never infer what the agent "must have" done.
- **Independence.** Never ask for or use the other annotator slot's work.
- **The user owns the submission.** Draft the annotation; the user reviews and
  submits it in Studio. Point out any judgment call that could reasonably go the
  other way so they can decide it.
- **Escalate, don't score, an ineligible pair** — both FAIL, no Gemini trajectory,
  or evidence the frozen task changed between rollouts.

## Verify, then stop

```bash
python3 tasks/gate.py tasks/<task-id>
```

Every BLOCK must PASS. Then re-open each cited reference and confirm it says what
the reason claims — the gate cannot check that. Hand back the prompt's deliverables.
