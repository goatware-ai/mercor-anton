# Prompt — annotate one Project Anton A/B pair

You are annotating Trajectory A and Trajectory B for one frozen Project Anton task,
and producing the evaluation-report JSON.

The judgment is yours to supply. The mechanical rules are in `tasks/gate.py`. Every
score and every rubric answer must be traceable to something in the trajectory, the
patch or the verification output. **An annotation is only as good as its evidence.**

| What | Lives in |
|---|---|
| Dimension 0, the eight dimensions and their 1–5 bands | `docs/03-task-workflow.md` §4 |
| Rubric rules: mapping, YES-is-good, legitimate sources | `docs/03-task-workflow.md` §5 |
| Preference scale and JSON shape | `docs/03-task-workflow.md` §6 |
| Evidence, validity, rationale style | `docs/04-golden-solution-guidance.md` |
| The Studio annotation screens | `docs/05-mercor-studio-walkthrough.md` |
| Doc contradictions and the working default | `FIELD-NOTES.md` §1 |
| JSON skeleton | `templates/annotation.json` |

## Before scoring: is this pair eligible?

Stop and escalate instead of annotating if any of these fails (`03` §3, §4):

- Both trajectories ran on **exactly the same harness, prompt, Harbor environment
  and starting commit**.
- **At least one is a Gemini trajectory.**
- **Not both are FAIL** on Dimension 0. If exactly one is FAIL, read FIELD-NOTES
  §1.1 first: it is acceptable only when the Gemini trajectory is the one that
  failed, and it still needs confirming before submission.
- Nothing in the frozen task changed between the two rollouts (`04`).

**Independence.** Do not look at, ask about, or share labels, rationales or
conclusions with the other annotator slot before submitting (`02` §3).

## Order of work

`03` and the walkthrough fix the order. Keep to it, because each step is meant to
be decided before the next one can bias it.

1. **Rubrics first.** Take the draft rubrics from task creation, or write them now
   from the prompt, the environment and the qualitative requirements, **before
   opening either diff** (FIELD-NOTES §1.7).
2. **Trajectory A, completely.** Read every step. Inspect the final patch separately
   from the process. Run or read the verification in the frozen environment. Compare
   what the agent *claimed* against what the output shows. Assign Dimension 0, then
   dimensions 1–8, recording evidence as you go.
3. **Trajectory B, the same way,** without re-scoring A.
4. **Answer the rubrics** for both.
5. **Only then compare.** `03`: "Do not select the pairwise preference before
   independently scoring both trajectories."

## Judging well

**Separate task defects from agent defects** (`04`, Annotation Validity). A failing
test can come from a wrong patch, a broken environment, an underspecified prompt or
a brittle test. Look at the underlying cause before charging it to the agent. If the
cause is the task, that is a finding to escalate, not a low score.

**Separate real solutions from gamed ones.** Hardcoded expected values, modified or
deleted tests, disabled assertions, special-casing the visible test inputs. These
score as failures however green the output looks. **Test weakening is zero-tolerance
on Dimension 7** (`03` §4).

**Judge the path, not just the diff.** Dimensions 5–8 are about the trajectory. On
Dimension 6, penalise redundant searches, thrashing, repeated failed strategies and
telescoping into an ad-hoc approach without scoping the alternative. The §7.1
reviewer checklist looks for exactly this. Expect fast convergence on localised
tasks and broader exploration on architectural ones.

**Check claims against output** on Dimensions 7 and 8. A final summary reporting
tests that were never run, or passing when the log shows failures, is
"hallucinated verification": a 1 on Dimension 8.

**Score to the bands, not to the gap.** Each trajectory gets the band its evidence
supports, read from `03` §4. Two strong trajectories can both be 5 on a dimension.
Don't push one down to make the comparison look decisive.

**Score blind to model identity.** Studio may show which model is which
(FIELD-NOTES §1.10). Use that only for the eligibility check above.

## Writing reasons

The walkthrough's rule: *a reason that restates the score ("architecture was weak")
isn't a reason — cite the step or the code.*

- One reason per dimension and per rubric covers **both** trajectories: what A did,
  what B did, and the evidence for each.
- Evidence means specific references: prompt excerpt, `file:line`, test name,
  trajectory step number, patch hunk, command output, final-message quote (`04`).
- Concise and factual. No generic commentary, no unsupported certainty, no repeated
  statements, no speculation about what the agent "probably" intended (`04`).

**Rubric statements**: binary, objectively verifiable, **YES is always the good
answer**, each mapped to exactly one dimension and one legitimate source (`03` §5).
Put more rubrics on the dimensions this task stresses: check `stressed_dimensions`
in `task.toml`. Reframe any statement where YES would be bad. "Did the agent write a
duplicate retry loop?" becomes "Did the agent reuse the existing RetryPolicy?".

## Final score and preference

- `final_quality_score_a` / `_b`: mean of dimensions 1–8, rounded to two decimals,
  with Dimension 0 excluded (FIELD-NOTES §1.4).
- `preference` must agree in direction with the final scores: the higher score is
  the preferred trajectory (`03` §7.1). Use `*_MUCH_BETTER` only when one side
  failed or introduced severe issues. Use `TIE` only when they are genuinely level.
- `comparative_rationale`: the two or three differences that decided it, each tied
  to evidence already cited in a dimension or rubric reason.

Use the dimension names and numbering from Studio and `03` §4, not the JSON example
in `03` §6 (FIELD-NOTES §1.2). **Do not fabricate reviewer, AutoQC or IAA values.**
Those are appended later by other people and systems.

## Files and checks

```
tasks/<task-id>/
├── harbor/                 the frozen package (from task creation)
├── trajectories/a.json     Harbor trajectory format, one file per trajectory
├── trajectories/b.json
└── annotation.json         from templates/annotation.json
```

```bash
python3 tasks/gate.py tasks/<task-id>      # every BLOCK line must PASS
```

The gate cannot check whether a reason is *true*. Before submitting, re-open each
cited step, line and test and confirm it says what the reason claims.

## Deliverables

1. The path to `annotation.json`.
2. The Studio annotation values in form order, in one fenced block: per trajectory,
   Dimension 0 and its reason, then dimensions 1–8 with reasons. Then the rubric
   answers, then the verdict.
3. Anything that should be escalated rather than scored: an ineligible pair, a task
   defect, a trajectory that gamed the tests.

Then stop.
