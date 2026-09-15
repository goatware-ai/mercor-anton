# ➡️ Task Workflow

> **General Task Workflow** — **Overview:** This document describes the workflow for creating a rigorous SWE task, generating or obtaining one agent trajectory, independently evaluating the same task and trajectory across two annotators, and submitting evidence-based annotations for reviewer QC.

## 1. Overview & Workflow Summary

As an annotator and reviewer team, your workflow consists of five sequential phases for each task:

1. **Task Creation:** Define a realistic, complex SWE task in **Harbor Format**, including qualitative_requirements that require evaluation beyond basic test execution.
2. **Trajectory Rollout & Part 1 Baseline Check:** Run at least **two independent agent rollouts** (Trajectory A and Trajectory B) per task. At least **one rollout must use a Gemini model**, and both must execute under **exactly the same harness, prompt, and Harbor environment**. At least one trajectory must earn PASS or PARTIAL. Gemini-Fail vs. a comparator is acceptable; reject only if both trajectories fail.
3. **Global Taxonomy Evaluation (Part 1 / 2/ 3):** Score each trajectory independently across **8 unified dimensions** on a **1–5 pointwise scale**, using bulleted observable signals and anti-patterns. The labeler needs to provide a reason for the scoring.
4. **Prompt-Specific Rubric Authoring:** Define **5–10 custom prompt-specific rubrics** formatted as binary **(YES | NO)** statements where **YES is always good to have**. Every rubric must map directly to one of the 8 global taxonomy dimensions, with labelers allocating more rubrics to the dimensions that matter most for that specific task.The labeler needs to provide a reason for the scoring.

## 2. Phase 1: Task Creation

A valid SWE evaluation task must require **verification, reasoning, and engineering judgment beyond basic functional correctness.** While standard automated tests verify execution, tasks must be sufficiently complex that human evaluators are needed to judge architectural cleanliness, code maintainability, trade-off soundness, and convention adherence.

### 2.1 General Complexity Requirement

**NOTE: Any SWE task is valid as long as it is sufficiently complex that its quality must be evaluated beyond functional correctness (unit tests passing).** Whether that complexity stems from system architecture, algorithmic performance, legacy codebase refactoring, concurrency safety, or multi-module dependency wiring, the task must challenge the agent's engineering discipline.

A valid task must require engineering judgment beyond a simple unit-test pass. Appropriate complexity may involve:

- Architecture or modular decomposition
- Multi-file repository reasoning
- Performance constraints
- Concurrency or ordering behavior
- API compatibility and downstream consumers
- Repository conventions and utility reuse
- Robustness, security, or failure semantics
- Migration sequencing and rollback safety
- Comprehensive test design
- Scope discipline in an underspecified MVP

Do not add artificial work merely to make a task appear difficult.

### Example Task Types to Consider:

| Task Type | Prompt Shape | Deterministic Gate | Qualitative Requirements |
|---|---|---|---|
| **feature_implementation** | Behavior request, no interface block | New behavior observable, existing tests hold | Fit with existing conventions, utility reuse over reinvention |
| **bug_fix_deterministic** | Symptom only, no repro steps | Repro flips, no regressions | Root cause addressed rather than symptom suppressed |
| **bug_fix_nondeterministic** | Intermittent symptom, no reliable repro | Failure rate over N runs drops below frozen bound | Correct concurrency or ordering reasoning, no sleep-based papering over |
| **refactor** | Refactor this codebase | All existing tests pass, public behavior byte-identical | The actual signal. Coupling reduced, boundaries improved, no dead path left beside the new one |
| **architecture_design** | Constraints and growth pressure, no target design | Artifacts build, stated interfaces resolve | Coherent decomposition, tradeoffs named and consistently resolved, failure modes anticipated |
| **mvp** | Product goal, deliberately underspecified | Builds, runs, satisfies stated interface, smoke path survives | Scope discipline, sane defaults, iteration-ready structure over premature generality |
| **codebase_migration** | Move code from X to Y | Both old and new paths verified, no data loss | Sequencing, rollback safety, incremental rather than big-bang |
| **performance_optimization** | Budget or SLA, no hint where the cost is | Behavior preserved, measured target met | Correct bottleneck identified, no correctness traded for speed |
| **test_writing** | Workflow or behavior described at a high level, agent finds what to test and where | Manifest matches the patch, all listed tests pass at baseline, all fail under mutation, so no extraneous tests | Comprehensiveness of behavior coverage (mandatory), placement in the codebase, suite conventions, local helper and fixture reuse |

Do not create new category names. If multiple categories seem relevant, select the primary requested outcome and describe secondary characteristics in the task metadata.

### 2.2 Harbor Task Definition Format

Tasks should be defined in standard Harbor format with optional tests folder.

## 3. Phase 2: Generating Trajectories & Part 1 Baseline Check

For every Harbor task, you must generate and record **at least two candidate trajectories** (Trajectory A and Trajectory B):

- **Goal Completeness Requirement:** At least one trajectory must earn PASS or PARTIAL. Two acceptable configurations. Both trajectories PASS or PARTIAL, or Gemini FAILs while the comparator earns PASS or PARTIAL. Reject only when both fail, since neither trajectory then demonstrates enough of the goal to support rubric authoring. The asymmetric case produces easy preference labels, which is accepted deliberately, because the rubrics extracted from a Gemini failure against a working comparator are the artifact we want.
- **Mandatory Gemini Requirement:** At least one of the two candidate trajectories must be generated by a **Gemini-powered SWE agent**. You may adjust the approved temperature or retry the rollout to obtain a Gemini trajectory that meets the Goal Completeness requirement.
- **Strict Controlled Environment:** Both rollouts must be executed using **exactly the same harness, exactly the same user prompt, and exactly the same Harbor Docker environment and starting git commit**. Any variance in artifact quality or trajectory efficiency must be strictly attributable to agent reasoning and execution. The environment should be clean, self-contained and internet access disabled.

## 5. Phase 3: Prompt-Specific Rubrics (5–10 Binary YES/NO Statements)

To prevent automated judges from overfitting to generic patterns, annotators must define **5–10 Prompt-Specific Rubrics** for each task *before* scoring.

### 5.1 Mapping to Global Taxonomy & Labeler Category Allocation Rule

**IMPORTANT Mandatory Mapping & Flexible Allocation:** Every single prompt-specific rubric must map directly to one of the **8 Global Dimensions** defined in Section 4.

Labelers decide how many rubrics to allocate to each category based on the task's unique focus. Different tasks emphasize different engineering challenges—labelers should define more binary rubrics in the categories that matter most for that specific task (e.g., allocating 4 rubrics to Architecture for a complex design task, or 4 rubrics to Verification for a concurrency bug fix).

### 5.2 Binary YES/NO Formatting Rule

Each prompt-specific rubric must be framed as an objectively verifiable **binary question/statement where YES is always good to have**.

- **Correct (YES is good):** "Did the agent reuse RetryPolicy from src/common/retries.py instead of writing a custom loop?" → **YES / NO**
- **Correct (YES is good):** "Did the agent explicitly raise SchemaValidationError when an invalid struct was passed to parse_record()?" → **YES / NO**
- **Incorrect (Do not frame negatively):** "Did the agent write a duplicate retry loop?" (Here YES would be bad—reframe it so YES is positive).

### 5.3 Sources and Legitimacy of Prompt-Specific Rubrics

Prompt-specific rubrics **must not be created out of nowhere.** Each rubric must be derived from one of three legitimate sources:

1. **Explicitly Stated in the Prompt:** Any constraint, architectural instruction, or non-functional requirement directly specified by the user.
2. **Implicitly Inferrable from the Environment:** Project-specific patterns, existing utility modules, logging frameworks, or exception hierarchies present in the repository.
3. **Common Engineering Knowledge (Senior Engineer Judgment):** Fundamental SWE principles appropriate for the task's context. For example:

- *Production Software Context:* It is common knowledge that an agent cannot write a hacky, unreadable, unmaintainable hack if modifying core production software that will be used broadly.
- *MVP / Demo Context:* It is common knowledge that an agent should avoid over-abstraction or multi-layered enterprise complexity if creating a quick MVP script or demo.

### 5.4 Example List of 8 Binary Prompt-Specific Rubrics (Payment Retry Task)

1. **[Dim 2 - Architecture]** "Did the agent integrate with the existing RetryPolicy abstraction in src/common/retries.py rather than creating a duplicate custom retry decorator?" → **YES / NO**
2. **[Dim 2 - Algorithmic Trade-off]** "Did the agent use an O(1) hash set lookup for deduplicating retry keys rather than an O(n^2) nested list scan?" → **YES / NO**
3. **[Dim 3 - Conventions]** "Did the agent use project structured logging in src/common/logging.py rather than raw print() statements or stdlib root loggers?" → **YES / NO**
4. **[Dim 4 - Robustness / Fail-Fast]** "Did the agent fail fast by immediately raising GatewayAuthenticationError on HTTP 401/403 responses rather than masking the error or retrying?" → **YES / NO**
5. **[Dim 4 - API Stability]** "Did the agent preserve the public signature of GatewayClient.send_payment() without breaking backwards compatibility for callers?" → **YES / NO**
6. **[Dim 3 - Change Discipline]** "Is the final diff surgical, containing zero gratuitous formatting changes to untouched adjacent lines?" → **YES / NO**
7. **[Dim 6 - BFS Scoping]** "Did the agent inspect the existing retry helpers in src/common/ before writing its retry handler?" → **YES / NO**
8. **[Dim 7 - Debug Hygiene]** "Did the agent remove all temporary debugging logs and test scripts before submitting the final patch?" → **YES / NO**

## 4. Phase 4: Global Taxonomy & 1–5 Scoring Rubrics

The evaluation taxonomy is structured into **Three Parts** across **8 Unified Dimensions**:

- **Part 1: Goal Completeness & Baseline Non-Triviality** (Dimension 0) — assesses whether the pair meets the eligibility rule in Section 3.
- **Part 2: Code & Artifact Quality** (Dimensions 1–4) — evaluates the final deliverable as a standalone product.
- **Part 3: Process & Trajectory Quality** (Dimensions 5–8) — evaluates the agent's behavior and methodology throughout the session.

Each dimension in Part 2 and Part 3 is scored on a **pointwise 1–5 scale** (higher is better). All observable signals and anti-patterns are presented as concise bullet points.

## Review Each Trajectory Independently

For A and then B:

- Read the complete trajectory.
- Inspect the final patch separately from the process.
- Run or review required verification in the frozen environment.
- Compare agent claims with actual output.
- Assign Dimension 0 status.
- Score Dimensions 1–8.
- Record evidence for every decision.

Do not select the pairwise preference before independently scoring both trajectories.

## Apply Dimension 0: Goal Completeness

Dimension 0 is an eligibility gate and is not included in the numeric final score.

- **PASS**: Complete or sufficiently complete. The solution works as intended by the task creator, with at most minor non-functional issues.
- **PARTIAL**: Core functionality works as intended, but one or two minor non-blocking edge cases or optional requirement was missed OR Usable after some user modification in non-execution based env.
- **FAIL**: Fundamentally incomplete or broken. Failed to achieve the core functional goal.

**If both trajectories are FAIL, or the comparator is FAIL while Gemini passes, stop and escalate the pair-selection error.**

## Score Dimensions 1–8

Assign one integer from 1 to 5 for every dimension and trajectory. Higher is better.

| Score | General meaning |
|---|---|
| 5 | Excellent, complete, senior-level execution with no meaningful defect |
| 4 | Strong execution with only minor inconsequential issues |
| 3 | Adequate and functional with noticeable but non-critical weaknesses |
| 2 | Major weaknesses, incomplete reasoning, fragile behavior, or material repair needed |
| 1 | Fundamentally broken, unsafe, deceptive, or unusable |

### Dimension 1: Correctness and Goal Fulfillment

Evaluate stated behavior, edge cases, regressions, and non-execution-based requirements.

- **5:** Fully correct; all material deterministic and qualitative requirements are satisfied.
- **4:** Correct on the intended path with one minor inconsequential issue.
- **3:** Core behavior works, but a noticeable non-blocking gap remains.
- **2:** Major requirements are missing or substantial user repair is needed.
- **1:** Core behavior is incorrect, deceptive, or unusable.

### Dimension 2: Architecture, Modularity, and Trade-off Soundness

Evaluate structure, abstraction level, algorithm/data-structure choices, and context-appropriate trade-offs.

- **5:** Senior-level design, clean boundaries, sound trade-offs, and appropriate extensibility.
- **4:** Strong design with only minor imperfections.
- **3:** Functional but somewhat ad hoc, inefficient, over-engineered, or under-designed.
- **2:** Excessive coupling, poor abstraction, naive critical-path strategy, or mismatched design.
- **1:** Severely broken architecture, circular dependencies, irrational design, or extreme over-engineering.

### Dimension 3: Codebase Conventions, Utility Reuse, and Diff Discipline

Evaluate project idioms, helper reuse, duplication, surgical scope, and cleanup.

- **5:** Maintainer-quality code, project infrastructure reused, surgical diff, and no debug residue.
- **4:** Conventions followed and major utilities reused with minimal noise.
- **3:** Minor inconsistency, duplication, or unnecessary churn.
- **2:** Frequent convention violations, substantial reinvention, or a noisy patch.
- **1:** Repository conventions ignored, core infrastructure duplicated, or unrelated files changed without justification.

### Dimension 4: Robustness, Safety, and API Stability

Evaluate failure semantics, malformed inputs, resources, concurrency, security, and compatibility.

- **5:** Comprehensive safeguards, appropriate failure behavior, and preserved APIs.
- **4:** Strong handling of expected failures and compatibility requirements.
- **3:** Primary cases handled, but rare edge conditions or awkward compatibility remain.
- **2:** Fragile behavior, masked errors, unsafe exception handling, or unplanned breaking changes.
- **1:** Severe bugs, deadlocks, leaks, vulnerabilities, silent corruption, or unhandled API breakage.

### Dimension 5: Instruction Following and Scope Discipline

Evaluate explicit requirements, negative constraints, scope boundaries, and workflow rules.

- **5:** Every material instruction followed with no scope creep.
- **4:** All important boundaries followed with at most one benign addition.
- **3:** Core requirements met, but a minor instruction is missed or scope is slightly stretched.
- **2:** A material boundary or negative instruction is violated locally.
- **1:** Core constraints are blatantly ignored or severe unauthorized scope is introduced.

### Dimension 6: Planning, Research, and Tool Proficiency

Evaluate decomposition, navigation, solution-space exploration, right-sized research, tools, and adaptation.

- **5:** Clear dependency-aware plan, right-sized exploration, precise tools, and effective adaptation.
- **4:** Clear plan, systematic navigation, effective tools, and consideration of the primary alternative.
- **3:** Correct area reached, but avoidable detours or premature commitment occur.
- **2:** Little planning, chaotic navigation, excessive research, premature telescoping, or repeated failed strategy.
- **1:** Aimless loops, blind edits, repeated rereading, or inability to make progress.

Expect rapid convergence on localized tasks and broader solution-space exploration on complex architectural tasks.

### Dimension 7: Verification and Testing Discipline

Evaluate verification evidence, edge-case coverage, test integrity, debug hygiene, and honesty.

- **5:** Reproduction created when applicable; happy paths and edge cases verified; focused tests added; results reported accurately; no debug residue.
- **4:** Appropriate functional verification and sound tests with no weakening.
- **3:** Provided verification used adequately, but little additional edge-case coverage is added.
- **2:** Weak checks, missed obvious cases, debug artifacts, or inadequately explained failures.
- **1:** No meaningful verification, failing output ignored, tests weakened/deleted, assertions disabled, or expected results hardcoded.

Test weakening is a zero-tolerance violation.

### Dimension 8: Communication and Reporting Quality

Evaluate intermediate communication and the final summary.

- **5:** Risks explained before execution; concise milestone updates; blockers surfaced early; final summary accurately reports changes, tests, rationale, and limitations.
- **4:** Risks and progress communicated clearly; final summary accurate and concise.
- **3:** Adequate communication and factual summary with minor omissions.
- **2:** Poor risk communication, unexplained silence, repetitive chatter, or vague final summary.
- **1:** Silence during destructive operations, concealed blockers, hallucinated verification, or deceptive/absent final summary.

---

## 6. Phase 5: Pairwise Evaluation & JSON Annotation Reporting

After scoring Part 1, Part 2, and Part 3 across all dimensions and evaluating the 5–10 binary prompt-specific rubrics for both Trajectory A and Trajectory B, annotators must compare them side-by-side and submit the final evaluation report in **JSON format**.

### 6.1 Overall Preference Scale

Select exactly one preference rating comparing Trajectory A to Trajectory B:

- **A_MUCH_BETTER**: Trajectory A is vastly superior in functional correctness, code elegance, or verification discipline; B failed or introduced severe issues.
- **A_BETTER**: Both completed the task, but A demonstrated superior trade-offs, cleaner code, or right-sized research.
- **TIE**: Both trajectories performed equally well (or equally poorly) across qualitative and functional dimensions.
- **B_BETTER**: Trajectory B demonstrated superior engineering quality or process discipline.
- **B_MUCH_BETTER**: Trajectory B is vastly superior; Trajectory A failed or exhibited severe flaws.

# Reviewer Instructions

**IMPORTANT Independent Reviewer (Task Auditor) Requirement:** To ensure high dataset integrity, an **Independent Reviewer (Task Auditor)** must review and approve the task definition, baseline completeness, and rubrics before final annotation package submission.

### 7.1 Independent Reviewer Audit Checklist

The Independent Reviewer must verify and sign off on the following:

- **Task Complexity & Non-Triviality:** Confirm that the Harbor task challenges the agent beyond simple unit-test correctness (e.g., architecture, performance, conventions, safety).
- **Controlled Environment & Model Selection:** Confirm that at least one trajectory used a Gemini model, and both executed under **exactly the same harness, prompt, and Harbor environment** (Section 3).
- **Part 1 Goal Completeness Parity:** Confirm that both Trajectory A and Trajectory B achieve baseline Goal Completeness without dramatic discrepancy (no PASS vs FAIL pairs).
- **5–10 Binary Prompt-Specific Rubrics Validity:** Confirm that 5–10 binary prompt-specific rubrics are defined, objectively verifiable, mapped to the 8 global dimensions, framed so YES is always good to have, and derived from legitimate sources (prompt, environment, or senior engineering common knowledge).
- **Over-Researching & Telescoping Audited:** Confirm that the labeler properly penalized turns wasted on redundant searches, thrashing, or telescoping into an ad-hoc approach without scoping alternatives (Dimension 6).
- **Surgical Patch Audited:** Confirm that the git diff was audited for extraneous reformatting, unsolicited refactoring, or dead code (Dimension 4).
- **Test Integrity Audited:** Confirm that neither agent weakened or deleted existing tests to fake success (Dimension 7).
- **Final Score & Preference Consistency:** Confirm that final_quality_score_a and final_quality_score_b are consistent with the pairwise preference (higher score = preferred trajectory).
- **JSON Schema Compliance:** Confirm that the JSON report includes task_type, Part 1 status, "reason" fields for all prompt-specific rubrics and global dimensions, binary "answer_a"/"answer_b" (YES/NO) values, and a structured comparative rationale.

# Required Delivery and AutoQC

## Required Delivery

Each completed task delivers:

- One complete Harbor task package.
- One Harbor trajectory JSON for Trajectory A.
- One Harbor trajectory JSON for Trajectory B.
- One evaluation-report JSON.
- Final code artifacts or patch references for A and B.
- Verification output for A and B.
- Reviewer approval metadata.
- System-generated AutoQC/IAA metadata when available.

## Required Evaluation-Report Shape Example

### Required JSON Reporting Format

Trajectory should be in the **https://www.harborframework.com/docs/agents/trajectory-format** format. Each trajectory should have a unique json file.

Annotators must submit the evaluation using the following JSON schema. Note that every object in prompt_specific_rubrics and global_dimensions includes a required "reason" field explaining the rationale:

```json
{
  "task_id": "swe-complex-042",
  "task_type": "architecture_design",
"trajectory_a_path": "<path_or_id_to_the_first_trajectory>",
"trajectory_b_path": "<path_or_id_to_the_second_trajectory>",
  "part_0_goal_completeness": {
    "status_a": "PASS",
    "status_b": "PASS",
    "reason": "Both trajectories achieved the baseline retry handler requirement wi[truncated]
  },
  "prompt_specific_rubrics": [
    {
      "rubric_id": "ps_rubric_1",
      "mapped_dimension": 1,
      "source": "COMMON_ENGINEERING_KNOWLEDGE",
      "statement": "Did the agent integrate with the existing RetryPolicy abstracti[truncated]
      "answer_a": "YES",
      "answer_b": "NO",
      "reason": "Trajectory A discovered and extended RetryPolicy; Trajectory B wro[truncated]
    },
    {
      "rubric_id": "ps_rubric_2",
      "mapped_dimension": 3,
      "source": "EXPLICIT_PROMPT",
      "statement": "Did the agent fail fast by immediately raising GatewayAuthentic[truncated]
      "answer_a": "YES",
      "answer_b": "NO",
      "reason": "Trajectory A raised GatewayAuthenticationError on 401/403; Traject[truncated]
    }
  ],
  "global_dimensions": [
    {
      "dimension_id": 1,
      "name": "Architecture, Modularity & Trade-off Soundness",
      "score_a": 5,
      "score_b": 3,
      "reason": "Trajectory A reused existing abstractions cleanly; Trajectory B wr[truncated]
    },
    {
      "dimension_id": 2,
      "name": "Codebase Conventions & Utility Reuse",
      "score_a": 5,
      "score_b": 2,
      "reason": "Trajectory A followed structured logging conventions; Trajectory B[truncated]
    },
    {
      "dimension_id": 3,
      "name": "Robustness, Safety & API Stability",
      "score_a": 5,
      "score_b": 2,
      "reason": "Trajectory A failed fast on authentication errors; Trajectory B ma[truncated]
    },
    {
      "dimension_id": 4,
      "name": "Change Discipline & Patch Reviewability",
      "score_a": 5,
      "score_b": 3,
      "reason": "Trajectory A was surgical; Trajectory B reformatted 40 untouched a[truncated]
    },
    {
      "dimension_id": 5,
      "name": "Instruction Following & Scope Discipline",
      "score_a": 5,
      "score_b": 5,
      "reason": "Both agents obeyed all explicit instructions and negative constrai[truncated]
    },
    {
      "dimension_id": 6,
      "name": "Planning, Research & Tool Proficiency",
      "score_a": 5,
      "score_b": 2,
      "reason": "Trajectory A surveyed existing helpers before coding; Trajectory B[truncated]
    },
    {
      "dimension_id": 7,
      "name": "Verification, Testing Discipline & Communication",
      "score_a": 5,
      "score_b": 4,
      "reason": "Trajectory A added unit tests for jitter math and removed temporar[truncated]
    },
    {
      "dimension_id": 8,
      "name": "Communication & Collaboration",
      "score_a": 5,
      "score_b": 3,
      "reason": "Trajectory A proactively explained the retry trade-off; Trajectory[truncated]
    }
  ],
  "final_quality_score_a": 5,
  "final_quality_score_b": 3,
  "pairwise_evaluation": {
    "preference": "A_MUCH_BETTER",
    "comparative_rationale": "Trajectory A demonstrated senior-level SWE discipline[truncated]
  }
}
```

Do **NOT** fabricate Reviewer or AutoQC values.

## AutoQC Checks

**AutoQC** should verify:

- Required files and valid JSON
- Task and trajectory identifier consistency
- Frozen prompt, harness, environment, and commit consistency
- At least one Gemini trajectory
- Both statuses in {PASS, PARTIAL}
- Exactly eight global dimensions with integer scores from 1 through 5
- Correct final-score arithmetic and two-decimal reporting
- Five to ten valid binary rubrics
- Valid task-format, task-category, source, answer, and preference enums
- Pairwise direction consistency
- Required reasons and evidence
- Reviewer outcome before delivery

After both reviewed annotations are complete, AutoQC appends IAA metadata. Reviewers do not edit this output. The team may manually audit a sample of completed tasks to verify that automated comparison remains reliable.
