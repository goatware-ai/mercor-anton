# Mercor Studio Walkthrough

> **Studio Walkthrough** — Read below to walk through the studio workflow that is expected of you.

### 1. Start off by reviewing the instructions.

*[Screenshot: Studio "How to annotate this task" instructions panel]*

> **How to annotate this task**
>
> **What you do**
>
> 1. **Task authoring.** Write a non-trivial SWE task in Harbor format. It has to demand judgement beyond passing tests: architecture, conventions, safety, verification discipline.
> 2. **Rubrics.** Define 5 to 10 binary questions where YES is always the good answer. Each maps to one of the eight dimensions and is derived from the prompt, from the environment, or from common engineering knowledge. Do not invent them.
> 3. **A/B pair.** Studio generates two rollouts under the same harness, prompt, environment and starting commit, at least one of them Gemini.
> 4. **Scoring.** For each trajectory: Dimension 0 (PASS / PARTIAL / FAIL), the eight dimensions on 1 to 5 with a written reason each, the rubric answers, and a final quality score.
> 5. **Verdict.** Rank the two trajectories and justify the comparison.
>
> **The eight graded dimensions**
>
> 1. Correctness
> 2. Architecture, Modularity & Trade-off Soundness
> 3. Codebase Conventions & Utility Reuse
> 4. Robustness, Safety & API Stability
> 5. Instruction Following & Scope Discipline
> 6. Planning, Research & Tool Proficiency
> 7. Verification & Testing Discipline
> 8. Communication: In-flight & Final Summary Quality
>
> Dimension 0, Goal Completeness, is a gate rather than a score.
>
> **Rules**
>
> - You cannot see the other annotator's work, and that is deliberate.
> - You cannot see which model produced A and which produced B.
> - A written reason is required on every dimension and every rubric.

### 1. Author your own unique task.

Write an original SWE task in Harbor format. It must require judgement that passing tests alone can't confirm: architecture, codebase conventions, failure semantics, verification discipline. If a competent agent could pass it by writing code until tests go green, it's too easy. Look at Samples to see what a good prompt looks like.

***Done when***\*:\* the prompt states the goal, the constraints, and what must not change, and you can name which of the eight dimensions it stresses.

*[Screenshot: Studio "0 · Task definition" panel with the "Task prompt (native, runs the rollouts)" User message]*

> **0 · Task definition**
> Provisional. Input shape still to be agreed on the call with Aahil.
>
> **Task prompt (native, runs the rollouts)** — User:

````text
Work entirely inside /workspace. You have a shell with Python; you have no internet access.

Create `exporter.py` containing exactly this implementation, which is currently in production:

```python
class ChunkedCsvWriter:
    FLUSH_THRESHOLD = 4

    def __init__(self, path):
        self.path = path
        self._buf = []
        self._rows_written = 0

    def write_row(self, row):
        self._buf.append(",".join(str(c) for c in row))
        if len(self._buf) >= self.FLUSH_THRESHOLD:
            self._flush()

    def _flush(self):
        if not self._buf:
            return
        with open(self.path, "a") as fh:
            fh.write("\n".join(self._buf) + "\n")
        self._rows_written += len(self._buf)
        self._buf = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def export(rows, path):
    with ChunkedCsvWriter(path) as w:
        for r in rows:
            w.write_row(r)
    return path
```

Users report that exports occasionally come back truncated, with no error raised. It does not
reproduce on large datasets.

Your job:
1. Write a test that reproduces the truncation and fails against the code above.
2. Fix the root cause.
3. Re-run the test and show it passing.

Constraints:
- Do NOT change the public signature of `export(rows, path)` or `ChunkedCsvWriter.write_row(row)`.
- Do NOT raise `FLUSH_THRESHOLD` or add a retry to mask the problem.
- A partial export must fail loudly rather than silently return a short file.

Finish with a short summary of the root cause and what you changed.
````

### 1. Task Details

- Put "Terminal Bench" as the Task Format.
- Leave "Golden Solution" as null

*[Screenshot: Studio "Task" form filled in for task swe-smoke-002 (note: the Task format dropdown in the screenshot shows SWE BENCH)]*

> **Task**
>
> - **Task ID\*** — `swe-smoke-002`
> - **Task format\*** — Proposal, Options of Task Type. Orthogonal to task type: the format is where the task lives, the type is what it asks for. — Value: `SWE BENCH`
> - **Task type\*** — The proposal's Task Type (Detailed) table; each option carries its prompt shape, deterministic gate and qualitative requirement. Note the delivery JSON §6.2 example uses a different vocabulary (INFRA_DESIGN / SWE_BENCH) — that is the task format, captured separately. Open with Adam. — Value: `Bug Fix Deterministic`
> - **Task prompt\*** — The prompt both rollouts receive. State explicit constraints: files that must not be modified, required interfaces, scope boundaries. Note this duplicates the task's native prompt, which is what the agents actually run, so keep the two identical until that duplication is resolved. — Value: (same task prompt as above)
> - **Qualitative requirements\*** — Requirements a unit test cannot settle. These are what make the task non-trivial. — Value: "Root cause is the missing flush on context-manager exit, not the threshold. The fix must keep fail-fast semantics: a short export raises rather than returning quietly. Reuse the existing _flush() rather than adding a second write path."
> - **Repository** — (empty)
> - **Base commit** — The same starting commit for both rollouts. Guide §3: any difference in artifact quality or trajectory efficiency must be attributable to agent reasoning, not to a different starting state. — (empty)
> - **Golden solution\*** — Reference solution. Proposal, phase 1 and the deliverables list: the golden solution is a tasker output. — Value: "\_\_exit\_\_ never flushes, so a final buffer below FLUSH_THRESHOLD is discarded. Flush in \_\_exit\_\_ and assert \_rows_written equals the number of rows submitted."

### 1. Trajectories

Run two trajectories on the same harness, prompt, environment, and starting commit. At least one must be Gemini. Wait for both to reach Completed.

Score in this order:

- Binary rubrics - you can answer these as each trajectory finishes.
- Per trajectory: Dimension 0 (PASS / PARTIAL / FAIL, the gate), then the eight dimensions 1–5. Judge both the final answer *and* the step 0 → step n path, not just the diff.
- Verdict: rank A vs. B and justify the comparison against specific evidence.

***Done when***\*:\* every dimension and every rubric item has a written reason. A reason that restates the score ("architecture was weak") isn't a reason - cite the step or the code.

*[Screenshot: Studio "Run Bundle" dropdown open, showing bundle options]*

> **Run Bundle** — Select a bundle...
> - A/B pair — Gemini 3.1 Pro (A) then Claude Opus 4.8 (B) (2 runs)
> - A/B pair — Gemini 3.1 Pro (A) then GPT-5.6-Sol (B) (2 runs)

*[Screenshot: Studio "2 · Trajectories A / B" panel with Run Trajectory (status "complete", 2 completed), Run Bundle / Models inputs, Trajectory History table, and Task Rubric table]*

> **2 · Trajectories A / B** — **Run Trajectory**: Execute harness trajectories for this task. Controls: Run Bundle (Select a bundle...), Models (Add models...), Run Trajectory.
>
> **Trajectory History**
>
> | Trajectory | Annotated | Status | Harness | Model | Platform | Elapsed Time |
> |---|---|---|---|---|---|---|
> | 2 | | Completed | ReAct Toolbelt Agent (Web Disabled) | Trajectory 2 | code exec + filesystem + sql v3 | 3m 14s |
> | 1 | | Completed | ReAct Toolbelt Agent (Web Disabled) | Trajectory 1 | code exec + filesystem + sql v3 | 1m 34s |
>
> **Rubric** — Criteria used to evaluate trajectory success for this task (buttons: Google Sheets, Open in New Tab, Add Rubric Item)
>
> **Task Rubric** — Criteria specific to this task (view: Structured / Spreadsheet)
>
> | Index | Verifier Type | Criteria | Depends on |
> |---|---|---|---|
> | 1 | Prompt-specific rubric (binary YES/NO) — LLM judge | Did the agent flush the remaining buffer on context-manager exit? | |
> | 2 | Prompt-specific rubric (binary YES/NO) — LLM judge | Did the agent preserve chunking rather than flushing on every row? | |
> | 3 | Prompt-specific rubric (binary YES/NO) — LLM judge | Does a short export now raise rather than return silently? | |
> | 4 | Prompt-specific rubric (binary YES/NO) — LLM judge | Did the agent leave export() and write_row() signatures unchanged? | |
> | 5 | Prompt-specific rubric (binary YES/NO) — LLM judge | Did the agent show the test failing before the fix and passing after? | |

You can complete the binary rubrics as the trajectories finish. Then index by model A and model B to evaluate the model's final answer and the step 0 → step n trajectories.

### 5. Complete the 8 dimension scoring before you submit your task.

*[Screenshot: Studio "Trajectory A / B" panel, Model A tab (completed), showing PROMPT, FINAL ANSWER, DIFF and LOGS sections]*

> **Trajectory A / B** — tabs: Model A | Model B — Model A `completed`
>
> **PROMPT** — User: "Work entirely inside /workspace. You have a shell with Python; you have no internet access. Create `exporter.py` containing exactly this implementation, which is currently in production: ```python class ChunkedCsvWriter:" (Show more)
>
> **FINAL ANSWER** — "I have completed the task within the sandbox environment.
> **1. Reproducing the Issue**
> I created a test script `test_exporter.py` that writes a dataset with a number of rows that is not a multiple of the `FLUSH_THRESHOLD` (e.g., 5 rows, while the threshold is 4). When run against the original `exporter.py`, the test failed and reproduced the silent truncation issue. Test code (`test_exporter.py`):" (Show more)
>
> **DIFF** (collapsed)
>
> **LOGS** (Search logs..., Environment, Expand all):
> - **Step 0** — 0.0 other: queue_monitor work_unit: batch_id=None campaign_id=camp_75099d23386f4394ab7596a5ea538da...; 0.1 other: Running model vertex_ai/gemini-3.1-pro-preview with agent ReAct Toolbelt Agent (Web Disabled); 0.2 other: Starting ReAct Toolbelt agent with vertex_ai/gemini-3.1-pro-preview; 0.3 configure: Loaded 8 MCP tools (toolbelt starts empty)
> - **Step 1** — 1.0 step: Starting step 1; 1.1 reasoning: \*\*My Thought Process Regarding the `exporter.py` Issue\*\*
> - **Step 2** — 2.0 step: Calling 1 tool(s): toolbelt_list_tools; 2.1-2.2 tool_call: `toolbelt_list_tools` Meta-tool: toolbelt_list_tools; 2.3 step: Starting step 2; 2.4 reasoning: \*\*My Thought Process on Tool Augmentation\*\*
> - **Step 3** — 3.0 step: Calling 1 tool(s): toolbelt_add_tool; 3.1-3.2 tool_call: `toolbelt_add_tool` Meta-tool: toolbelt_add_tool

*[Screenshot: Studio "Your Annotation" form with Dimension 0 select and 1–5 sliders plus reason boxes for each dimension]*

> **Your Annotation**
>
> - **Dimension 0 · Goal completeness\*** — The gate, not a graded dimension. (Select...)
> - **Dimension 0 · reason\***
> - **1 · Correctness\*** — Note: the full 1-5 bands for this dimension appear in neither the spec nor the proposal; the proposal defers to the vendor annotation guide. These anchors are provisional until that guide arrives. — 1 = core functional goal not achieved … 5 = works as intended, no functional gaps
> - **1 · reason\***
> - **2 · Architecture, Modularity & Trade-off Soundness\*** — 1 = severely broken or irrational architecture … 5 = senior-level engineering judgment
> - **2 · reason\***
> - **3 · Codebase Conventions & Utility Reuse\*** — 1 = disregards conventions, duplicates infrastructure … 5 = indistinguishable from senior maintainer code
> - **3 · reason\***
> - **4 · Robustness, Safety & API Stability\*** — 1 = severe bugs, deadlocks, leaks, swallowed errors … 5 = expert failure semantics and defensive programming
> - **4 · reason\***
> - **5 · Instruction Following & Scope Discipline\*** — 1 = blatantly violates negative instructions … 5 = zero scope creep, obeys every constraint
> - **5 · reason\***
