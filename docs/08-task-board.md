# Studio Task Board

> **Maintained by Claude.** This page is not part of the spec. It tracks the Anton
> tasks visible on the Studio board and what an audit of each existing annotation
> found. Update it whenever a new board export arrives or a task changes state.

**Snapshot:** 2026-09-15, from the Studio board export `task board - Sheet1.csv`
(10 rows, all Claimable).

**Independence:** the board shows labels written by other annotators. Before you
claim a task, confirm in `#anton-general-bf1` whether those labels are a draft you
are meant to revise or the other slot's work. If they are the other slot's work,
don't claim a task whose annotation has been read here.

---

## 0. Claimed

No task is claimed.

### The Studio "How this task works" page (read 2026-09-15, all six steps)

1. **Read the task (tab B).** Browse the bundle: `environment/`, `solution/`,
   `tests/`, `instruction.md` and `task.toml`. Set **Task type** by classifying it
   from the metadata in `task.toml`.
2. **Score rollout A (tab C).** Read the agent solution, then the trajectory. Score
   dimensions **2 to 9** on 1–5, each with a written reason, and give a final quality
   score for the side. Dimension 0 is pre-filled from the recorded run.
3. **Score rollout B (tab D).** Same process. Score B on its own merits before
   comparing the two.
4. **Rubrics (tab E).** Write **8 to 15** binary questions where YES is always the
   good answer. Each maps to one dimension and comes from the prompt, the
   environment or common engineering knowledge. Record how many you wrote in
   **Rubric count**, then answer every one for both sides with a reason citing
   evidence. Rubrics 1–8 are required and 9–15 are optional.
5. **Pairwise comparison (tab F).** Give an overall preference of A against B and
   write a comparative rationale. The preference has to agree with your two final
   quality scores.
6. **AutoQC and submit (tab G).** Run AutoQC, fix whatever it flags, then submit.
   Passing sends the task to review; failing returns it to you with the issues.
   Tab H is the independent reviewer's, not yours.

The full observed flow is in [09-studio-flow.md](09-studio-flow.md).

Studio tabs: A · How this task works → B · Task bundle / Task Details →
Trajectory Viewer (Agent solution A, Agent solution B) → Rubric (create) / Rubric
count → Deliverable AutoQC → Submit review. The right-hand panel has Annotation A,
Annotation B, Pairwise verdict and More.

**Contradiction on screen:** the instructions call Dimension 0 "read-only for you",
but the Dimension 0 (B) field says *"The annotator must verify and correct PASS /
PARTIAL / FAIL verdict as needed. For non-grandfathered tasks, a verdict and
written reason are required before Submit for Final QC."* Working default: verify
it and write a reason anyway.

---

## 1. What a Studio task looks like (observed, not in the docs)

- **Every Claimable task arrives fully populated:** prompt, two rollouts, eight
  dimension scores with reasons, rubrics, a preference and a rationale. The
  observed work is to revise an existing annotation, not to author a task. This is
  **unconfirmed**; ask before relying on it.
- **QC note on some tasks:** *"Both Model A and Model B must have a rubric pass rate
  strictly below 75%… with 8 rubric items, each model may have at most 5 YES
  answers."* Only change an answer when the trajectory supports the change. The
  honest fix is to replace rubrics that both sides pass with rubrics that separate
  them, each still traceable to the prompt, the environment or senior-engineering
  knowledge.
- **Studio differs from `docs/` and FIELD-NOTES in these ways:**

| Topic | `docs/` / repo | Studio board |
|---|---|---|
| Dimensions | 0 gate + 1–8 (1 = Correctness) | 0 gate + **2–9**; no Dimension 1 column. 8 = Intermediate Communication & Risk Explanation, 9 = Final Summary & Presentation Quality |
| Rubrics per side | 5–10 | Up to 15 with a mapped dimension, plus 10 more slots (16–25) without one; most tasks use 8–15 |
| Rubric pass rate | no rule | Below 75% YES for each side (from the QC note) |
| Score scale | integers 1–5 | Mostly 1–5; some tasks use labels 🟣 Production ready / 🟢 Minor polish only / 🟡 Light rework needed / 🔴 Must redo |
| Harness | not specified | `opencode` ("Lighthouse Harbor (OpenCode) - terminal bench") or `terminus_2` (archipelago, with test results in the run ledger) |
| Models | at least one Gemini | `gemini-3.7-flash` paired with `claude-opus-5` or `gpt-5.6-sol` |
| Golden solution | `solution/solve.sh` | `solution/solution.patch` + sha256 + apply command |

---

## 2. Board

"YES A / B" is the count of YES rubric answers per side, with the pass rate in
brackets. **Bold** marks a side that breaks the 75% rule.

| # | Task ID | Type | Language · harness | A vs B | Dim 0 (A) | Preference | Final A / B | YES A / B | Verdict | Our status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `epoch-fenced-wal-shipping#model_ab` | bug_fix | Bash · opencode | Opus 5 vs Gemini | FAIL | TIE | 2 / 2 | 9/13 (69%) / 7/13 (54%) | Avoid | — |
| 2 | `mtls-mesh-gateway-chain-policy-repair#model_ab` | bug_fix | C/OpenSSL · opencode | Gemini vs Opus 5 | PASS | A_BETTER | 🟣 / 🔴 | **8/8** / **7/8** | Avoid | — |
| 3 | `replay-divergence-repair#model_ab` | bug_fix | Python · opencode | Gemini vs Opus 5 | PASS | B_BETTER | 3 / 4 | 5/8 (62%) / **8/8** | **First pick** | — |
| 4 | `tilted-xrd-ring-lattice-inversion#model_ab` | feature | Python · opencode | Gemini vs Opus 5 | PASS | B_BETTER | 3 / 4 | 7/10 (70%) / **10/10** | Possible | — |
| 5 | `actlens-causal-ablation-pipeline#model_ab` | bug_fix | Python · opencode | Gemini vs Opus 5 | PARTIAL | B_MUCH_BETTER | 2 / 5 | 5/12 (42%) / **12/12** | Hard | — |
| 6 | `sharded-lora-gradient-daemon-equivalence` | bug_fix | Python · opencode | GPT-5.6 vs Gemini | PASS | A_BETTER | 4 / 3 | **15/15** / 11/15 (73%) | Possible | — |
| 7 | `stripped-tx-framer-cycle-exact-rtl-clone` | feature | Verilog · opencode | Gemini vs Opus 5 | PASS | TIE | 4 / 4 | 9/14 (64%) / **11/14** | Avoid | — |
| 8 | `sep1-timezero-bundle-abstraction` | bug_fix | Python · terminus_2 | Gemini vs GPT-5.6 | PASS (3/3 tests both) | B_BETTER | 3 / 4 | **12/15** / **13/15** | **Backup pick** | — |
| 9 | `cyclic-reversible-token-lineage#model_ab` | bug_fix | SQL (DuckDB) · opencode | Opus 5 vs Gemini | PASS | A_BETTER | 5 / 4 | **15/15** / **15/15** | Avoid | — |
| 10 | `lantern-warrens-tablebase-blunder-audit` | feature | Python · terminus_2 | GPT-5.6 vs Gemini | PASS (4/4 tests both) | TIE | 3 / 3 | 11/15 (73%) / 11/15 (73%) | Possible | — |

"Our status" values: `—` (not claimed) · `claimed` · `in progress` · `submitted` ·
`returned` · `approved`.

---

## 3. Per-task audit notes

Each note lists the problems in the existing annotation that a revision has to fix.
A note is not a score for either trajectory.

### 1 · epoch-fenced-wal-shipping: Avoid
- A is FAIL, and the rationale says B also breaks a required behaviour (a staged
  transaction never converges through `cmd_recover`). **Both sides likely FAIL,
  which makes the pair ineligible.**
- 13 rubrics, and **none has a mapped dimension**.
- One reason still shows its edit history ("Revised upward now that the final
  summary is available").
- The reasons are detailed and cite functions and `smoke.sh` assertions. The TIE
  follows from the scores.

### 2 · mtls-mesh-gateway-chain-policy-repair: Avoid
- **Gemini PASS vs Opus FAIL.** `03` §4 says to escalate this case (FIELD-NOTES
  §1.1).
- Carries the QC note. A's rubrics are 8/8 YES and B's 7/8; most rubrics ask "did
  it fix defect X", which both sides did.
- B's rubrics 4 and 5 accept B's unverified final-message table as "stronger
  evidence", while B's Dimension 7 and 9 reasons call that table unverified.
- B is penalised for "opaque binary diffs", which is most likely a diff-viewer
  rendering artifact rather than agent behaviour.
- B's FAIL cause is never identified: Dimension 4 says "nothing… explains" it.
- Uses the label scale instead of 1–5.

### 3 · replay-divergence-repair: First pick
- Both sides PASS, the pair is eligible, and all 8 rubrics are mapped.
- Carries the QC note. B has 8/8 YES and needs to reach ≤5 while A stays ≤5 (A is
  at 5 now).
- The existing reasons already point to real B weaknesses to verify against the
  trajectory:
  - the spawn-mutation change was not requested and is only flagged at the end of
    B's final summary;
  - 14 of B's 50 turns have no narration;
  - REPORT.md has extra prose beyond the required single JSON block.
- **Inconsistency to settle:** B scores 5 on Dimensions 2 and 4 for the
  spawn-mutation hardening.
  - If the spec's trap paragraph requires that fix, A missed a requirement, and
    A's Dimension 5 score of 4 is wrong.
  - If it doesn't, B changed behaviour it wasn't asked to change, which should
    cost B on Dimension 5.
  - Check `spec/RULES.md` to decide.

### 4 · tilted-xrd-ring-lattice-inversion: Possible
- Both sides PASS. B is at 10/10 YES, which breaks the 75% rule (no QC note yet).
- Rubrics 9 and 10 have **no mapped dimension**, and one cell says `undefined`.
- B's patch leaves 88 scratch files. That is a real Dimension 3 issue with no rubric
  covering it.

### 5 · actlens-causal-ablation-pipeline: Hard
- Gemini PARTIAL (reward 0.0) vs Opus PASS, which the workflow allows.
- Carries the QC note. B is at 12/12 YES and needs ≤8 of 12, but B scores 5 on
  almost every dimension, so honest NO answers for B are scarce.
- A is PARTIAL with reward 0.0. Confirm which is right before scoring.

### 6 · sharded-lora-gradient-daemon-equivalence: Possible
- Both sides PASS. A is at 15/15 YES (100%); B is at 73%.
- Dimension 9 is 4 / 4 while the final scores are 4 / 3. Check that the final
  scores and Dimension 9 agree.
- 15 rubrics, all mapped.

### 7 · stripped-tx-framer-cycle-exact-rtl-clone: Avoid
- **The rubric evidence for A and B is swapped.**
  - A's Dimension 2 reason says A duplicates the LFSR recurrence (`ks_of`,
    `lfsr_step8`), but A's rubric 2 says A computes it once in `calc_lfsr_step`.
  - The rationale credits A with the 126 edge cases and "Two bugs worth flagging",
    but those appear under B's rubrics 9 and 11.
  - A's rubric 10 calls A silent, which the rationale says of B.
- **No rubric has a mapped dimension.** B is at 79%.
- All 14 rubric answers need redoing.

### 8 · sep1-timezero-bundle-abstraction: Backup pick
- Both sides PASS with real test results (3/3 each) in the run ledger. The pair is
  PASS/PASS, and all 15 rubrics are mapped.
- The rubrics already separate the sides (A NO on 7, 8, 15; B NO on 9, 10). Only
  A −1 and B −2 are needed to get under 75%, so this is the smallest honest
  revision on the board.
- A's trajectory is long: 85 calls and about 8,100 s.

### 9 · cyclic-reversible-token-lineage: Avoid
- Both sides PASS. Both are at **15/15 YES**, so the rubrics don't separate the
  sides at all. **None has a mapped dimension.**
- A scores 5 on every dimension. Check whether that holds up.

### 10 · lantern-warrens-tablebase-blunder-audit: Possible
- Both sides PASS with 4/4 tests each. Both are at 73%, which already meets the
  75% rule.
- **No rubric has a mapped dimension.**
- The TIE sits beside A scoring higher on 5 of 7 dimensions (29 vs 20 total),
  though the rationale explains the offsetting strengths. A reviewer may still
  challenge the TIE.

---

## 4. Reading a board export

Studio's CSV export has an **empty first row with no column names**. Columns are
0-indexed; this map was verified against the cell contents of the 2026-09-15 export.

| Column | Field |
|---|---|
| 0 | Task name |
| 1 | Task status |
| 2 / 3 | Created by / Updated by |
| 5 | Criteria count |
| 9 / 10 | Created at / Updated at |
| 12 | Task ID |
| 13 | Task type |
| 15 | Repository |
| 18 | Task category (opencode tasks) |
| 19 | Rubric count |
| 20 | Dimension 0 (A) |
| 21 | Harness |
| 22 | QC / transition note |
| 32 | Run ledger JSON: models, trajectory IDs, and test results for terminus_2 |
| 44 / 45 | Pairwise ranking / rationale (auto) |
| 59 | schema_version |
| 60 | Problem title |
| 61 | Language (terminus_2) or domain (opencode) |
| 62 | Difficulty |
| 63–68 | Verifier timeout, agent timeout, build timeout, CPUs, memory MB, storage MB |
| 74 / 75 | Solution status / provenance |
| 82 | Delivery target |
| 86 / 87 | Preference / comparative rationale |
| 88–101 | A: dimensions 2–8 as (score, reason) pairs |
| 102–146 | A: rubrics 1–15 as (answer, reason, mapped dimension) triples |
| 147 | A: final quality score |
| 148–161 | B: dimensions 2–8 |
| 162–206 | B: rubrics 1–15 |
| 207 | B: final quality score |
| 208 / 209 | A: Dimension 9 score / reason |
| 210 / 211 | B: Dimension 9 score / reason |
| 212–231 | A: rubrics 16–25 as (answer, reason) pairs |
| 232–251 | B: rubrics 16–25 |
| 252–255 | Transcript and artifact files (exported as `[object Object]`, so not usable) |

Empty cells export as `—` or as an empty string.

```python
import csv
rows = list(csv.reader(open("task board - Sheet1.csv", encoding="utf-8")))[1:]
for r in rows:
    yes_a = sum(r[102 + 3 * k] == "YES" for k in range(15))
    yes_b = sum(r[162 + 3 * k] == "YES" for k in range(15))
    print(r[12], r[86], r[147], r[207], yes_a, yes_b)
```

---

## Change log

- **2026-09-15:** first snapshot, 10 Claimable tasks. Recommended first pick #3,
  backup #8.
- **2026-09-15:** first task claimed. Recorded Studio's "How this task works" steps.
- **2026-09-18:** that task was unassigned; its local folder and drafts were removed.
