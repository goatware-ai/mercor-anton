# 🥇 Golden Solution Guidance

> **Task and Trajectory Quality Guidance** — **Overview:** This section defines the quality bar for a complete Trajectory QC package. A strong package contains a realistic SWE task, one complete shared trajectory, two independent evidence-based evaluations, and the artifacts required for reviewer QC and final JSON delivery.

## Required Task and Trajectory Artifacts

Every submission must include the artifacts required by Studio. Depending on the task, these include:

- Created task prompt and metadata
- Repository snapshot and starting commit
- Environment and test instructions
- Complete trajectory logs for A and B
- Final patches or unified diffs for A and B
- Test and evaluation output for A and B
- global-dimension scores and prompt-specific rubric responses
- Final quality scores and pairwise preference
- Evidence references and rationales
- Required JSON output

Do not include unrelated local files, caches, environment folders, scratch notebooks, stale logs, or temporary debugging artifacts.

## Frozen Task and Controlled A/B Pair

Trajectory A and Trajectory B must use the exact same frozen task configuration. Before generating the selected rollouts, freeze the prompt, repository snapshot, starting commit, environment, tests or verification instructions, harness, tool permissions, and resource limits.

Do not change the task or evaluation criteria after seeing rollout outcomes. If any frozen task artifact changes, discard affected rollouts and regenerate them before annotation. Only approved model identity and model-configuration differences may vary between A and B.

## Evidence and Reproducibility

A reviewer must be able to determine:

- What task was created and why it is sufficiently non-trivial
- Which repository snapshot and environment were used
- Which models and harness produced Trajectories A and B
- What each agent did during its trajectory
- What each final patch or artifact changed
- Which tests or evaluations were run for A and B
- Which evidence supports each rubric answer

Use specific references such as prompt excerpts, file paths, line numbers, test names, trajectory steps, patch hunks, command output, and final agent messages.

## Annotation Validity

The annotation must distinguish task-design issues from agent-performance issues. A failed test may result from an incorrect patch, a broken environment, an underspecified task, or a brittle test. Inspect the underlying evidence before assigning a judgment.

The annotation must also distinguish a genuine task solution from a trajectory that passes visible tests by hardcoding, modifying tests, disabling assertions, or exploiting weak tests. Evaluate the actual behavior and engineering quality of each artifact.

## What "good" looks like

| Area | Strong package | Not acceptable |
| --- | --- | --- |
| Task creation | Realistic SWE task requiring meaningful judgment | Artificial or trivial task with one obvious change |
| Shared task control | Both annotators receive the same frozen task package | Different prompts, commits, tests, or task versions |
| Trajectory capture | Complete commands, edits, patch, and final output | Informal summary without the actual trajectory |
| Verification | Reports actual commands, test outcomes, and logs | Claims success without output |
| Rubric evaluation | Cites trajectory, patch, and test evidence | Judges only from final pass/fail status |
| Independence | Annotators submit without coordinating judgments | Annotators share labels or rationale before submission |
| Submission | Includes all required artifacts and follows the current schema | Omits evidence or invents JSON fields |

[EXT] Imperium | SWE Trajectory QC Annotation Instruction Document

## Rationales and Annotator Notes

Write concise, factual rationales. Explain what the task, trajectory, patch, and verification evidence show and why they support the selected rubric answer. Do not include generic commentary, unsupported certainty, repeated statements, or personal speculation.

## LLM Policy

You may use LLMs for research, coding assistance, testing, and review. You may not use them as a substitute for your own judgment when annotating trajectories.

The expert owns the solution. You tell the LLM what to do, not "claude/codex take the wheel" - and that matters more as tasks get harder. If asked to defend a decision, "the LLM suggested it" is not an acceptable answer.

Obvious LLM slop results in an instant offboarding, even on a first offense after a great track record. Reviewers should never have to check whether your docstring, comments, or code contain slop; it must be understood by all parties that this is not allowed. Slop includes verbose generic comments, contradictory docstrings, stale references to reviewer feedback, fake certainty, irrelevant abstractions, and code that looks plausible but does not match the task.

## Reviewer Handoff

The reviewer should be able to answer these questions quickly:

\1. Is the created task complete, realistic, and sufficiently non-trivial?

\2. Did both annotators evaluate the same frozen task and trajectory?

\3. What evidence supports the rubric answers?

\4. What was the verified trajectory outcome?

\5. What uncertainty or disagreement remains?

\6. Is the package ready for final JSON review and delivery?
