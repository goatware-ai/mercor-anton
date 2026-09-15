---
name: review-task
description: Audit a Project Anton task package and annotation the way the Independent Reviewer does — task non-triviality, controlled A/B pair, Dimension 0 parity, rubric validity, over-research, surgical patch, test integrity, score/preference consistency and JSON compliance. Use when the user runs /review-task, or asks to review, audit, QC or self-check an Anton task or annotation before submitting.
---

# review-task

Review an Anton task and its annotation against the reviewer's own checklist.

The criteria are `docs/03-task-workflow.md` §7.1 and the "Reviewer Handoff"
questions in `docs/04-golden-solution-guidance.md`. Read both before starting. Where
the checklist contradicts the rest of the docs (it does, on FAIL pairs and on which
dimension owns the surgical-patch audit), apply `FIELD-NOTES.md` §1 and say which
entry you applied.

## 1. Run the gate

```bash
python3 tasks/gate.py tasks/<task-id>
```

A BLOCK is a finding. Do not repeat the gate's output line by line — summarise it.

## 2. Walk §7.1, item by item

For each item, read the evidence yourself — the annotation's claims are what is
under review, not a source.

1. **Task complexity & non-triviality** — does the task need judgment beyond a unit
   test pass? Compare the prompt against `docs/06-samples.md`: vague, solution-leaking,
   trivial, unbounded, unverifiable?
2. **Controlled environment & model selection** — one Gemini trajectory; same
   harness, prompt, environment, commit.
3. **Dimension 0 parity** — per FIELD-NOTES §1.1.
4. **Rubric validity** — 5–10, binary, objectively verifiable, YES-is-good, mapped,
   from a legitimate source. Flag any rubric that could not be answered from the
   diff and trajectory, or that was invented rather than derived.
5. **Over-research & telescoping** — open the trajectory. Were wasted turns,
   thrashing or unscoped ad-hoc approaches penalised on Dimension 6?
6. **Surgical patch** — open both diffs. Extraneous reformatting, unsolicited
   refactoring, dead code — reflected in the score?
7. **Test integrity** — did either agent weaken, delete or skip tests, or hardcode
   expectations? If so, is Dimension 7 at 1?
8. **Score & preference consistency** — higher final score is the preferred side.
9. **JSON compliance** — `03` §6 shape, reasons everywhere.

Then spot-check at least three cited references per trajectory: open the step, line
or test and confirm the reason is accurate. A reason that cites something that does
not say that is the most serious annotation defect there is.

## 3. Report

Lead with a verdict: **approve**, **revise**, or **escalate** (task defect or
ineligible pair). Then one line per failed or doubtful item, each with the evidence
and the specific change needed. Items that passed get no commentary. Do not edit the
task or annotation unless the user asks — a review reports; it does not fix.
