# Studio Flow: fetch, review, annotate, submit

> **Maintained by Claude.** This page is not spec. It describes how an Anton task is
> actually worked in Studio, as observed on 2026-09-15, and how to get everything
> into this repo so it can be reviewed properly. Update it whenever Studio behaves
> differently from what's written here.

Studio's own summary, from "How this task works": *"You are not authoring the task.
The task, both agent rollouts, and the goal-completeness call arrive already seeded.
Your job is to judge the two rollouts against each other."*

---

## 1. Where each piece of a task lives

| Piece | Studio location | API endpoint (`api.studio.mercor.com`) | Local path after `studio.py har` |
|---|---|---|---|
| Task: prompt, models, Dim 0 seed and automated check, patches, final answers, current annotation | whole page | `GET /tasks/{task_id}` | `studio/export.json`, `meta.md`, `prompt.md`, `patch_*.diff`, `final_answer_*.md`, `annotation-current.md` |
| Rubric criteria, with source and mapped dimension | Rubric (create) | `GET /verifiers/task/{task_id}` | `studio/annotation-current.md` |
| **Task bundle** (10 files, including `environment/prompt_statement.md`) | Tab B · Task bundle | `GET /snapshots/task/{id}/input-files` (list), then `/file-url?file_path=` → signed S3 `GET` | `harbor/<same path>` |
| **Trajectories** (every message) | Trajectory Viewer → Model A / Model B | `GET /trajectories/{traj_id}` (A/B from the run ledger) | `trajectories/transcript_A.json`, `_B.json` |
| Trajectory logs | Trajectory Viewer → LOGS | `GET /trajectory-logs/list/{traj_id}` | `trajectories/logs_A.json`, `_B.json` |
| **The real `agent.patch`** (not the reconstructed diff) | nowhere; the page never downloads it | `GET /snapshots/trajectory/{traj_id}` then `/file-url` → signed S3 | `trajectories/a_agent.patch`, `b_agent.patch` — **extension only** |
| World rubric ("Lighthouse Overall Result") | Rubric (create) → World Rubric | `GET /verifiers/world/{world_id}` | `studio/world-rubric.json` |
| **Reviewer feedback** | inline comments, tab H | `GET /inline-review-comments/task/{task_id}` | `studio/review-feedback.md` |
| History (every version, full field snapshot) | History | `GET /tasks/{task_id}/history` | `studio/history.json` |
| **AutoQC results** | Deliverable AutoQC | `GET /qc-audits/?subject_id=…` | `studio/autoqc.md`, `qc-audits.json` |
| **AutoQC rules** (the exact text graded against) | not shown | `GET /qc-specs/?…` | `studio/qc-specs.json` → [docs/10-autoqc-rules.md](10-autoqc-rules.md) |
| **The form itself**: every field, the 1–5 band text per dimension, options, word minimums | the right-hand Annotation A / B / Pairwise panels | `GET /worlds/{world_id}` → `task_schema.fields` | `studio/form-schema.json` → [docs/11-annotation-form.md](11-annotation-form.md) |

The right-hand panel's **values** (scores, reasons, rubric answers, verdict) come
with the task and land in `studio/annotation-current.md`. Its **definition** (help
text, bands, limits) comes from the world.

The task export JSON (the page's export button) is a subset: only the first two
rows, with trajectories as unusable S3 links.

---

## 2. Fetching a task: do this first, every time

Work in `tasks/<task-id>/`. The task-id is the Task ID without `#model_ab`. From
Windows the folder is
`\\wsl.localhost\Ubuntu\home\klayt\projects\mercor-anton\tasks\<task-id>`.

### 2.1 Extension capture (primary: one click)

Install once: [tools/studio-capture/README.md](../tools/studio-capture/README.md).

1. Open the task page and wait for it to finish loading.
2. Click **⬇ Capture task for review** (bottom-left). Wait for **✅ Saved**.
3. Run:

   ```bash
   python3 tasks/studio.py har "/mnt/c/Users/klayt/Downloads/studio-capture_<…>.har"
   python3 tasks/studio.py check tasks/<task-id>
   python3 tasks/studio.py rules tasks/<task-id>/studio/qc-specs.json   # only when the AutoQC spec versions change
   ```

The extension requests every piece in §1 directly, so no tab-clicking is needed.
`har` prints `! capture error` for any request that failed and `missing …` for
anything absent. If you see either, reload the page and capture again.

### 2.1b DevTools HAR (fallback if the extension fails)

1. Open the task page and press **F12**, then open the **Network** tab. Tick
   **Preserve log**, then reload (**F5**).
2. Make the page load every piece:
   - click **every** file in tab B;
   - on **Model A** and the **Model B** tab, open DIFF and LOGS, then click
     **Expand all**;
   - open **Deliverable AutoQC** and **History**.
3. Click **Export HAR** (sanitized) and save it to Downloads. Then run the same
   `har` and `check` commands.

**Hygiene for both:** the files contain no cookies, auth headers or signed URLs
(checked 2026-09-15), but they do contain task content. Keep them in Downloads,
**never commit them** (`*.har` is git-ignored), and delete them when the task is
done.

### 2.2 After every Save Changes in Studio

Studio may store something different from what you typed. For example,
`field_ta_dim4_score_b` is saved as `"3"`. Re-read what was stored with either:

- a quick **export JSON**, then `python3 tasks/studio.py unpack "<export.json>"` and
  `check`; or
- a new **extension capture**, then `har` and `check`. This also picks up new AutoQC
  results.

### 2.3 Manual fallbacks (only if a HAR can't be recorded)

- **Transcripts:** the ↗ icon on the Model A/B card, or the right panel's MORE ▾.
- **Bundle:** click each file in tab B, click inside the editor, press Ctrl+A then
  Ctrl+C, and paste into `harbor/<same path>`.
- **Reviewer feedback and AutoQC:** copy the text into `studio/review-feedback.md`
  and `studio/autoqc.md`.
- Don't copy the LOGS list by hand. The rows are collapsed and only partly drawn,
  so a copy loses content.

### 2.4 The extension, and when to fix it

Confirmed allowed by tooling support (2026-09-15). Its requests are the endpoint
table in §1. If Studio changes an endpoint, `capture.js` gets errors for that
request. Update the table and `tools/studio-capture/capture.js` together, re-copy
the extension (README), and add a §6 line.

---

## 3. Annotation flow

Studio's tabs set the order: A read → B task → C score A → D score B → E rubrics →
F pairwise → G AutoQC and submit. H is the reviewer's. Our steps map onto them.

| # | Step | Studio | Done when |
|---|---|---|---|
| 0 | **Claim one task.** Open History: has it been reviewed before? | Actions → Claim | `docs/08-task-board.md` §0 row added |
| 1 | **Fetch** everything: extension capture (§2.1), then `har` and `check` | ⬇ Capture task for review | `har` prints no `missing` or `! capture error` lines |
| 2 | **Returned task?** Read `studio/review-feedback.md` and the failing checks in `studio/autoqc.md` first. Each point becomes a to-do in `notes.md` | History, tab H, Deliverable AutoQC | every reviewer point and failing AutoQC check has a planned fix |
| 3 | **Eligibility and Dimension 0.** Compare the seeds with `field_score_*`, the automated `field_part1_disposition`, and `tests/config.json`. Both FAIL means an ineligible pair: ask in `#anton-general-bf1`, then **Flag Defective Task**; don't score it | Annotation A/B → Dimension 0 | a verdict and a written reason for each side, or the task is flagged |
| 4 | **Read the task.** Prompt, `task.toml` (set **Task type** from its metadata), tests (what FAIL_TO_PASS actually checks), golden patch | tab B, Task Details | Task type set; `notes.md` lists what the prompt explicitly requires |
| 5 | **Draft or review rubric criteria** from the prompt, the environment and common engineering knowledge, before reading either patch closely (FIELD-NOTES §1.7). A returned task already has criteria: test each one against those three sources | Rubric (create) | 8–15 criteria, each with a source and a dimension 2–9 |
| 6 | **Score A.** Read the patch, then the transcript. Dimensions 2–9 on 1–5 plus the final score. Reasons cite **A's own** steps, files and output, never B's findings | Annotation A | `check` shows no "other side" warning for A |
| 7 | **Score B** the same way, on its own merits | Annotation B | same |
| 8 | **Answer every rubric** for both sides with evidence. Each side's YES rate must be **below 75%** (≤5 of 8, ≤7 of 10, ≤11 of 15). Get there by writing rubrics that separate the sides, never by changing an answer the evidence doesn't support | Rubric panels | `check` shows the rates below 75% |
| 9 | **Pairwise verdict.** The label is fixed by the final-score gap A − B: 0 → TIE, ±1 → *_BETTER, ±2 or more → *_MUCH_BETTER (AutoQC `aq_c1`). Choose the final scores honestly and the label follows; write the rationale from evidence already cited | Pairwise Verdict | `check` shows the exact label |
| 10 | **Draft in the repo, then paste into Studio.** Keep the full text in `tasks/<task-id>/annotation-draft.md`. Save Changes, re-export, `unpack`, `check` | Save Changes | `check`: 0 BLOCK |
| 11 | **Self-review:** `/review-task`. Re-open every cited step and line | — | every citation confirmed |
| 12 | **AutoQC.** Run it, fix what it flags, re-run until 17/17. Navigation checklist all green | Deliverable AutoQC, Submit review | 17/17 and no ✗ in Navigation |
| 13 | **Submit for Final QC.** Update the board status. When review comes back, add a FIELD-NOTES §3 line and, if a script could have caught it, a `studio.py` check | Submit for Final QC | status `submitted` in docs/08 |

**Evidence rule for this form:** a reason cites the trajectory step or record, a
`file:line` or patch hunk, a test name, or quoted command output. An agent's final
message is a *claim*. Use it as evidence only for Dimensions 8 and 9, or when the
transcript confirms it.

---

## 4. Studio facts (observed 2026-09-15)

- **Scores:** dimensions 2–9 and the final quality score are `likert_scale` 1–5:
  **1 🔴 Must redo · 2 🟠 Substantial rework · 3 🟡 Light rework needed ·
  4 🟢 Minor polish only · 5 🟣 Production ready**. The band text for each
  dimension is in [11-annotation-form.md](11-annotation-form.md), and it is what
  Studio shows the annotator.
- **Every dimension reason needs at least 15 words** (`min_word_count`). That is
  the "Length limits" line in the Navigation checklist. `studio.py check` blocks a
  shorter one.
- **The final quality score is its own field**, not a computed mean. The preference
  must then match the gap between the two final scores.
- **Score type bug:** a score stored as a string (`"3"`) counts as missing. The
  Navigation checklist shows *"4 · Robustness, Safety & API Stability (B)
  required"*. Fix it by re-selecting the value in the dropdown.
- **Rubrics:** 8–15 (1–8 required). Each is a Task Rubric "Prompt-specific rubric
  (binary YES/NO)" with verifier type **LLM judge**. A World Rubric "Lighthouse
  Overall Result (all-or-nothing task score)" (programmatic) applies to every task.
  **Rubric count** is a separate required dropdown.
- **Dimension 0:** the form says "read-only for annotators", but the help text says
  the annotator must verify it and give a reason before Submit for Final QC. The
  export carries an automated check (`field_part1_reason*`,
  `field_part1_disposition`: `BOTH_PASS_OR_PARTIAL`, `REJECT_BOTH_FAIL`, …).
- **Reconstructed patches:** when the harness didn't capture a diff, the patch
  fields say *"Reconstructed from the agent's edit/write tool calls … Hunk offsets
  are RELATIVE … shell-based edits are not represented."* Such a diff can show a
  block added and then removed, or leave out files the agent changed through the
  shell. Treat those as capture artifacts: confirm against the transcript before
  charging them to the agent.
- **Transcripts:** `trajectory_messages[N]` is what annotations cite as
  "record N". `har` renders each transcript as `trajectories/A.md` / `B.md` with
  `## [N]` headings. For externally imported rollouts, tool-call **arguments are
  empty (`{}`)**. Outputs are kept but commands aren't, so don't claim what
  command an agent typed.
- **AutoQC:** the page says "Your task is only deliverable when you pass all 17/17
  test cases". The gate is the **Annotation Quality QC** spec (v11, 14 blocking
  checks). Its full text is in [10-autoqc-rules.md](10-autoqc-rules.md). Runs before
  spec v10 had 17 checks, including a blocking "Dimension 0 Matches The Recorded
  Reward" that has since been removed: upstream seed faults now go to the
  non-blocking reviewer audit.
- **Checks that commonly fail:**
  - `aq_a1` rubric **atomicity**: a statement joining parts that could get
    different answers ("opens in a new tab with noopener **and** percent-encodes
    the path") fails. Split it into two rubrics.
  - `aq_a4`: the **Gemini side's** YES rate must be below 75%. Reviewers also
    require it for the other side.
- **Reviewer returns** arrive as an inline review comment
  (`/inline-review-comments`). The export JSON doesn't include them, but a HAR does.
- **Non-blocking audits** run after submission: *Annotation Quality QC (Reviewers)*
  with 35 checks, and *(Annotator Advisory)* with 11. They're worth reading before
  submitting, because they describe what gets a task sent back.
- **Navigation checklist** (Submit review): "Before you submit", required fields
  per dimension and side, "Length limits: N · reason (A/B)" for each reason,
  "AutoQC failures resolved", "AutoQC up to date".
- **Actions:** Submit for Final QC · Unclaim · **Flag Defective Task**.
- **Lifecycle** (from History): Seed → Claimable → Annotating → Final QC / Review
  → In Review → (returned) Annotating → Claimable → Annotating (next claimant).
  `_remediated` in a name, together with an earlier In Review in History, marks a
  returned annotation.

---

## 5. Remediating a returned task

1. Read the reviewer feedback and any QC note. If neither is visible, ask in
   `#anton-general-bf1` for the return reason before editing. Don't guess.
2. `check` the existing annotation. Its BLOCK lines are the mechanical defects.
3. Re-verify the previous annotator's claims one by one against the transcripts.
   Keep a reason only if you can confirm its citation yourself. Rewrite everything
   else.
4. Watch for the usual defects, seen across the 2026-09-15 board:
   - Dimension 0 contradicting the recorded score;
   - one side scored using the other side's findings;
   - rubric evidence taken from the agent's own final message;
   - rubric answers written against the wrong trajectory;
   - rubrics missing a mapped dimension;
   - YES rates of 75% or more;
   - a TIE or preference that doesn't match the final scores;
   - capture artifacts (binary or reconstructed diffs) charged to the agent.

---

## 6. Fetch methods that worked

One line per task: which method produced the files.

- **2026-09-15 · deusdata-codebase-memory-mcp-863:** sanitized HAR (79 MB, no
  cookie or auth headers). `har` got the task, 9 of 10 bundle files, transcript and
  logs for A, the reviewer comment, 8 history versions, 5 AutoQC audits and 8 QC
  specs. Missed B's transcript and logs (Model B tab not opened) and
  `environment/prompt_statement.md` (not clicked).
- **2026-09-15 · same task, second HAR** (225 MB, 983 requests, sanitized): got
  B's transcript and logs too. Everything except `prompt_statement.md`.
- **2026-09-15 · tools/studio-capture v1.0.0 built.** Tested only in simulation
  (replaying this task's HAR): the `har` output was byte-identical. First live
  capture: pending. Record the result here.
