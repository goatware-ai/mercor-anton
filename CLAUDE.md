# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

The working repo for **Project Anton | SWE Trajectory QC Annotation** on Mercor Studio.
Contributors author a complex SWE task in Harbor format and run two agent rollouts on
it, Trajectory A and Trajectory B, with at least one from Gemini. They then score
both trajectories on eight dimensions, answer 5–10 task-specific YES/NO rubrics, and
submit one pairwise preference as JSON. A reviewer audits each annotation.

Three kinds of work happen here:

1. **Creating a task**: prompt, frozen Harbor package, qualitative requirements,
   golden solution. Follow [task-creation-prompt.md](task-creation-prompt.md), or
   run `/create-task`.
2. **Annotating an A/B pair**: eligibility check, scores, rubrics, preference,
   JSON. Follow [annotation-prompt.md](annotation-prompt.md), or run
   `/annotate-task`.
3. **Reviewing**: audit a task and annotation against the reviewer checklist. Run
   `/review-task`.

## Source hierarchy

- **[docs/](docs/) is the spec.** Read the relevant page before answering rather
  than working from general knowledge of SWE-bench or Terminal-Bench conventions.
  Highest-value pages:
  - [03-task-workflow.md](docs/03-task-workflow.md): task types, Dimension 0, the
    eight dimensions with 1–5 bands, rubric rules, preference scale, JSON shape,
    reviewer checklist, AutoQC. The densest file.
  - [04-golden-solution-guidance.md](docs/04-golden-solution-guidance.md): quality
    bar, frozen A/B pair, evidence, validity.
  - [05-mercor-studio-walkthrough.md](docs/05-mercor-studio-walkthrough.md): the
    Studio screens and field help text.
  - [06-samples.md](docs/06-samples.md): five good and five bad prompts, with why.
  - [08-task-board.md](docs/08-task-board.md): the Studio board snapshot, observed
    Studio schema, per-task audit notes and the CSV column map. Maintained by
    Claude, not spec. Update it when a new board export arrives or a task changes
    state.
  - [09-studio-flow.md](docs/09-studio-flow.md): how a claimed Studio task is
    fetched (export JSON, transcripts, bundle, reviewer feedback, HAR), then
    reviewed, annotated and submitted. Maintained by Claude. **Start here for any
    claimed task.**
  - [10-autoqc-rules.md](docs/10-autoqc-rules.md): the exact AutoQC and reviewer-audit
    criteria, generated from Studio's QC specs. Where they disagree with the docs,
    these are what a submission is graded against.
  - [11-annotation-form.md](docs/11-annotation-form.md): the Studio annotation form
    itself — every field, the 1–5 band text per dimension, the option lists and the
    15-word minimum on reasons. Generated from the world's `task_schema`.
- **[FIELD-NOTES.md](FIELD-NOTES.md) wins where the docs contradict themselves or
  where Studio is observed to behave differently.** §1 lists twelve internal
  contradictions with a working default for each: which FAIL pairs are allowed,
  dimension numbering, the final-score formula, task format, golden solution, rubric
  timing, and more. Read it before settling any of those questions from a single doc
  page.
- **[templates/harbor-task/](templates/harbor-task/) is the reference
  implementation**: a complete working task built from the walkthrough's
  `swe-smoke-002` example. Copy its shapes, not its content.
- **[tasks/gate.py](tasks/gate.py) is the enforcement.** A rule it checks isn't
  restated in the prompts.

## Domain model

**The five phases** (`03` §1): task creation → two rollouts plus the Dimension 0
check → prompt-specific rubrics → scoring on eight dimensions → pairwise preference
and JSON. Reviewer audit follows.

**A task** is judged on whether two competent trajectories come out *measurably
different* on the qualitative dimensions, not on whether tests pass. It must need
engineering judgment beyond a unit-test pass, use one of the nine task types in
`03` §2.1 (never a new name), and follow that type's prompt shape, deterministic
gate and qualitative requirement.

**The frozen pair.** A and B share the harness, prompt, Harbor environment, starting
commit, tests, tool permissions and limits. Only model identity and approved model
configuration may differ. Any change to a frozen artifact discards the rollouts
(`04`). Rollouts run with internet disabled.

**Dimension 0** is a gate (PASS / PARTIAL / FAIL), not a score. Both FAIL is
ineligible. The rules for a single FAIL contradict each other across the docs, so
see FIELD-NOTES §1.1.

**The eight dimensions**, each an integer 1–5 with a written reason:
1 Correctness · 2 Architecture, Modularity & Trade-off Soundness ·
3 Codebase Conventions, Utility Reuse & Diff Discipline · 4 Robustness, Safety &
API Stability · 5 Instruction Following & Scope Discipline · 6 Planning, Research &
Tool Proficiency · 7 Verification & Testing Discipline (test weakening is
zero-tolerance) · 8 Communication & Reporting Quality.

**Rubrics**: 5–10, binary, YES always good, each mapped to one dimension and derived
from one of three sources: explicit in the prompt, implicit in the environment, or
common senior-engineering knowledge. Never invented.

**Reasons** cite the step or the code: prompt excerpts, `file:line`, test names,
trajectory steps, patch hunks, command output. A reason that restates the score is
not a reason.

## Layout

```
docs/                     the project docs (spec)
FIELD-NOTES.md            doc contradictions + observed behaviour; wins over docs/
task-creation-prompt.md   end-to-end prompt for authoring one task
annotation-prompt.md      end-to-end prompt for annotating one A/B pair
templates/harbor-task/    working reference Harbor task (swe-smoke-002)
templates/annotation.json evaluation-report skeleton, Studio dimension names
tasks/gate.py             local pre-submission gate (package + annotation)
tasks/studio.py           Studio capture/export unpacker + Studio-form checks
tools/studio-capture/     Chrome extension: one-click capture of a Studio task
tasks/<task-id>/          one folder per task — see below
drafts/, notes/           work in progress, per-task write-ups
.claude/skills/           create-task, annotate-task, review-task
```

```
tasks/<task-id>/
├── harbor/               task.toml, instruction.md, environment/, solution/, tests/
├── trajectories/         a.json, b.json (Harbor trajectory format)
└── annotation.json
```

**Tasks live under `tasks/` only**, never at the repo root. `task.toml`
`[metadata]` holds the Studio Task form (`task_id`, `task_format`, `task_type`,
`qualitative_requirements`, `repository`, `base_commit`, `golden_solution`) plus
`stressed_dimensions`. `instruction.md` *is* the task prompt, pasted into Studio
verbatim.

## Commands

```bash
python3 tasks/gate.py tasks/<task-id>        # every BLOCK line must PASS before submitting
python3 tasks/gate.py templates/harbor-task  # blocks only on its REPLACE author fields
python3 tasks/studio.py har "<file.har>"            # sanitized HAR -> studio/, harbor/, trajectories/ (primary fetch)
python3 tasks/studio.py unpack "<task-export.json>"  # Studio export -> tasks/<task-id>/studio/
python3 tasks/studio.py rules tasks/<task-id>/studio/qc-specs.json  # regenerate docs/10-autoqc-rules.md
python3 tasks/studio.py form tasks/<task-id>/studio/form-schema.json # regenerate docs/11-annotation-form.md
python3 tasks/studio.py check tasks/<task-id>        # Studio-form rules; 0 BLOCK before submitting
```

There's no Studio CLI. Rollouts, the Task form and the annotation form are all
submitted in the Studio web UI, which is reached through Okta on work.mercor.com.
Local Docker/Harbor runs of a package are for proving the deterministic gate before
rollouts.

## Standing rules

- **Don't change a frozen task after seeing rollouts.** Regenerate instead.
- **Tests enforce only what the prompt states.** Qualitative requirements are for
  annotators and rubrics. A test that picks one valid implementation is a hidden
  requirement.
- **Never fabricate** reviewer, AutoQC or IAA values, trajectory evidence, or test
  output. If something wasn't run, say so.
- **Independence:** never share labels, rationales or conclusions with the other
  annotator slot before submission.
- **One claimed task at a time.** Don't hoard.
- **Where to ask:** `#anton-general-bf1` for annotation questions,
  `#anton-tooling-support-bf1` for Studio. When an answer settles a FIELD-NOTES §1
  entry, update the entry with the date. When a returned task shows a mechanical
  rule, add it to `gate.py` in the same pass.
