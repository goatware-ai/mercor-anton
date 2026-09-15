# Project Anton — Field Notes

What has been learned by doing Anton tasks, as distinct from what [docs/](docs/) says.

**Precedence.** `docs/` is the spec for what a task and an annotation are. This file
wins wherever Studio, AutoQC or a reviewer is observed to behave differently from
the docs, and it records the working default wherever the docs contradict
themselves. Where this file and [tasks/gate.py](tasks/gate.py) both cover a rule,
the gate is the enforcement and this file is the reason.

**Status (2026-09-15):** no task has been through a review cycle yet. §1 is built
from a close read of the docs alone. §2–§4 are empty and fill in from real
submissions, one entry per cycle it cost. Do not add an entry from reasoning alone.
Measured or observed only.

---

## 1. Where the docs contradict themselves

Each entry gives the conflict, the working default we follow until told otherwise,
and whether it has been confirmed. Ask in **#anton-general-bf1** (annotation) or
**#anton-tooling-support-bf1** (Studio), then update the entry with the answer and
the date.

### 1.1 Can a FAIL trajectory be in the pair?

| Source | Says |
|---|---|
| `01-project-anton.md` | Both selected trajectories must be rated PASS or PARTIAL |
| `03-task-workflow.md` §1 and §3 | At least one must be PASS/PARTIAL; Gemini FAIL vs. a passing comparator is accepted deliberately; reject only if both fail |
| `03` §4, Dimension 0 | Escalate if both FAIL, **or the comparator FAILs while Gemini passes** |
| `03` §7.1 reviewer checklist | "no PASS vs FAIL pairs" |
| `03` AutoQC | "Both statuses in {PASS, PARTIAL}" |

**Working default:** aim for both PASS/PARTIAL. A Gemini FAIL vs. a passing
comparator is allowed by the workflow section, but AutoQC and the reviewer
checklist as written would both flag it, so ask before submitting one. Both FAIL,
or a non-Gemini FAIL, means regenerating. `gate.py` blocks both-FAIL and warns on
any FAIL. **Unconfirmed.**

### 1.2 Dimension numbering and names

Studio's annotation form and `03` §4 number them 1 Correctness · 2 Architecture ·
3 Conventions & Diff Discipline · 4 Robustness · 5 Instruction Following ·
6 Planning · 7 Verification · 8 Communication.

The JSON example in `03` §6 has no Correctness dimension. It shifts Architecture
to 1, adds "Change Discipline & Patch Reviewability" as 4, merges
"Verification, Testing Discipline & Communication" into 7, and has
"Communication & Collaboration" at 8.

**Working default:** Studio/§4 numbering and names. `gate.py` warns on a name
mismatch rather than blocking. **Unconfirmed.**

### 1.3 Which dimension owns diff discipline

`03` §4 puts surgical scope and cleanup under **Dimension 3**, and §5.4 maps its
"Change Discipline" rubric to Dim 3. The §7.1 reviewer checklist says the surgical
patch audit is **Dimension 4**. Similarly, the §6 JSON example maps a fail-fast
rubric to dimension 3, while §5.4 maps the same rubric to Dim 4.

**Working default:** §4's definitions. Diff discipline is 3, fail-fast and
API stability are 4. **Unconfirmed.**

### 1.4 Final quality score formula

AutoQC checks "correct final-score arithmetic and two-decimal reporting" but no doc
gives the formula. The §6 JSON example is consistent with an **unweighted mean of
the eight dimension scores**: A is all 5s → 5, and B is
3+2+2+3+5+2+4+3 = 24 / 8 = 3. The example prints integers, not two decimals.

**Working default:** mean of dimensions 1–8, rounded to two decimals. Dimension 0
is excluded (`03` §4: "not included in the numeric final score"). `gate.py`
blocks a mismatch. **Unconfirmed.**

### 1.5 Task format value

The walkthrough text says to enter **"Terminal Bench"**. Its screenshot shows
`SWE BENCH`, and Studio's help text mentions a delivery vocabulary of
`INFRA_DESIGN` / `SWE_BENCH`.

**Working default:** "Terminal Bench", the written instruction. **Unconfirmed.**

### 1.6 Golden solution

The walkthrough says "Leave 'Golden Solution' as null". The same Studio form marks
Golden solution as required and describes it as a tasker output.

**Working default:** fill it in with a short summary, and always ship
`solution/solve.sh` in the package. A reviewer can ignore a field they don't need,
but can't recover one that was never written. **Unconfirmed.**

### 1.7 When rubrics are written

`03` §5 says to define rubrics *before* scoring, and `04` says not to change
evaluation criteria after seeing rollout outcomes. `03` §3 says "the rubrics
extracted from a Gemini failure against a working comparator are the artifact we
want", and the walkthrough says rubrics can be answered as trajectories finish.

**Working default:** draft rubrics from the prompt, the environment and the
qualitative requirements before opening either diff. Answer them afterwards. Add a
rubric only if a trajectory exposes a requirement that was already implied by one
of the three legitimate sources, and say so in its reason. **Unconfirmed.**

### 1.8 Rubric `source` enum

The JSON example shows `EXPLICIT_PROMPT` and `COMMON_ENGINEERING_KNOWLEDGE`. The
third source, implicitly inferable from the environment, has no enum name anywhere.

**Working default:** `IMPLICIT_ENVIRONMENT`. **Unconfirmed**, so check what Studio
emits.

### 1.9 One trajectory or two

The overviews of `03` ("generating or obtaining one agent trajectory") and `04`
("one complete shared trajectory") describe a single trajectory. Every other
section requires two, A and B.

**Working default:** two. The single-trajectory wording looks left over from an
earlier version.

### 1.10 Model identity

The walkthrough's Rules say annotators cannot see which model produced A and B. The
Run Bundle labels ("Gemini 3.1 Pro (A) then Claude Opus 4.8 (B)") and Step 0 of the
logs ("Running model vertex_ai/gemini-3.1-pro-preview") show it, and the
asymmetric FAIL rule in §1.1 can't be applied without knowing it.

**Working default:** score blind. Read dimensions from the diff and the steps, not
the model name. Use model identity only to check pair eligibility.

### 1.11 Roles

`02` §3 assigns each task to two annotator slots. `02` §4.2 is headed "Annotator"
but describes the Task Creator. The walkthrough has the annotator author their own
task, run the pair and score it.

**Working default:** do what the Studio assignment says. When authoring, the
creator also annotates, and the second slot annotates independently.

### 1.12 Stale or inconsistent references

- `07-slack.md` and the `04` header call the project **Imperium**, and everything
  else says Anton. Channel names differ too: `02` says "#Anton-writers", `07` says
  `#anton-writers-5d4`.
- The $50 promotion in `02` ran through **8/18 6PM PST**, so it has expired as of
  this writing.
- `03` numbers its sections 1, 2, 3, 5, 4, 6 and cross-references "Section 4" for
  the eight dimensions.

---

## 2. Studio and Harbor behaviour

The manifest field names in [templates/harbor-task/task.toml](templates/harbor-task/task.toml)
follow the standard Harbor layout. Our docs don't pin them, so the first task
that uploads confirms or corrects them here.

*No entries yet.*

## 3. Review and AutoQC outcomes

One line per returned task: what came back, the reason given, what fixed it, and
whether a `gate.py` check was added.

*No entries yet.*

## 4. Task shapes and the A/B signal they produced

The Anton equivalent of a difficulty ledger. For each submitted task: task type,
which dimensions it was built to stress, the Dimension 0 pair it produced, and
whether the two trajectories actually differed on the stressed dimensions. A task
where both agents write the same diff produces no preference signal
(`06-samples.md`, bad sample 3). Record it here so the shape isn't proposed again.

*No entries yet.*
