# Prompt — build one Project Anton task

You are authoring **one** SWE task for Project Anton | SWE Trajectory QC Annotation:
a task prompt, its frozen Harbor package, its qualitative requirements and golden
solution, and the Studio form that goes with them.

This prompt carries the judgment that no check makes for you. It does not restate
the mechanical rules, because `tasks/gate.py` blocks them. Where a rule is enforced,
this file names it once and points at the file that owns it.

| What | Lives in | Role |
|---|---|---|
| The spec: task types, dimensions, rubrics, JSON | `docs/03-task-workflow.md` | authoritative |
| Quality bar, frozen A/B pair, evidence | `docs/04-golden-solution-guidance.md` | authoritative |
| The Studio screens, field by field | `docs/05-mercor-studio-walkthrough.md` | authoritative on Studio |
| What a good and a bad prompt look like | `docs/06-samples.md` | read every sample |
| Where those docs contradict each other, and the working default | `FIELD-NOTES.md` §1 | wins over `docs/` |
| A complete working reference task | `templates/harbor-task/` | copy its shapes |
| Mechanical rules | `tasks/gate.py` | run it; don't restate it |

Annotating the A/B pair afterwards is a separate prompt: `annotation-prompt.md`.

## Read in this order

1. `docs/06-samples.md`, all ten samples. The bad samples are the five ways a
   prompt fails, and each one has been written by someone who meant well.
2. `docs/03-task-workflow.md` §2 (task creation) and §4 (the eight dimensions).
   You are designing a task that separates trajectories on those dimensions, so
   know the 1–5 bands before you pick a concept.
3. `FIELD-NOTES.md` §1, then §4 for task shapes already tried.
4. `templates/harbor-task/`, every file.

## What decides whether the task is worth anything

An Anton task is not graded by pass rate. It is graded by **whether two competent
trajectories come out measurably different on the qualitative dimensions**. The
annotation is the product, and a task that gives the annotator nothing to compare
has no value however clean it is.

Two gates, in opposite directions:

- **Too easy.** One obvious change, and both agents make it identically. No
  preference signal, no useful rubrics (`06`, bad sample 3). The deterministic
  gate passing is not the bar. `03` §2: quality "must be evaluated beyond
  functional correctness".
- **Too unfair.** Vague, unbounded, dependent on systems the rollout can't reach,
  or impossible to verify from a frozen package (`06`, bad samples 1, 4, 5). Both
  trajectories FAIL, the pair is ineligible (`03` §3), and the rollouts are wasted.

**The target:** a task a competent agent can complete (PASS or PARTIAL), where the
*way* it is completed carries several decisions a senior engineer would make
differently from a hurried one. Per `03` §3, a Gemini FAIL against a working
comparator is accepted, because the rubrics it produces are exactly what the
project wants. Don't aim for that case, but a task sitting close to it is
well pitched.

### The design question

> Name the two or three places where a plausible trajectory and a senior trajectory
> diverge, and the dimension each one lands on.

If you can't name them, the task is too easy. For each one, check:

- **Does the prompt leave the decision to the agent?** If the prompt makes the
  choice, it is transcription (`06` bad sample 2).
- **Does the environment make the right choice discoverable?** If a
  convention, helper, exception hierarchy or logging module is meant to be reused,
  it has to exist in the repository. That is also what makes a rubric about it
  legitimate (`03` §5.3, source 2).
- **Is there a plausible wrong choice that still passes the tests?** That is what
  gives the annotator something to judge. Examples: a symptom suppressed instead of
  the root cause, a second write path beside the existing one, a sleep papering over
  a race, a dead path left beside the refactored one, tests weakened to go green.

The task-type table in `03` §2.1 lists, per type, the qualitative requirement that
*is* the signal. Start there. Pick the type by the primary requested outcome, and
never invent a new type name.

What does **not** make a task better, per `03` §2.1 and `06`: artificial work added
to look difficult, undefined qualities ("safe", "efficient", "scalable", "properly"),
unbounded scope, production systems or live traffic, or a target nobody can
reproduce.

## The prompt

`instruction.md` **is** the task prompt, and Studio's "Task prompt" field is pasted
from it verbatim. The walkthrough is explicit that the two must stay identical.

A strong prompt, per `06`'s creator takeaway, defines:

- **the requested outcome**: the goal or the symptom, depending on type. A
  `bug_fix_deterministic` prompt states the symptom with no repro steps. A
  `performance_optimization` prompt states the budget with no hint where the cost
  is. The "Prompt Shape" column of `03` §2.1 is binding;
- **observable behavior**: return values, defaults, state transitions, error
  semantics. Anything that decides whether a result is correct (`06` good
  samples 1–3);
- **boundaries**: files that must not be modified, interfaces that must not
  change, what is out of scope (Studio "Task prompt" help text);
- **important constraints**, stated as constraints rather than steps. "Do NOT raise
  `FLUSH_THRESHOLD` or add a retry to mask the problem" rules out the symptom fix
  without describing the root-cause fix.

And it leaves **implementation decisions to the agent**. Test it against bad sample 2:
if a reader could write the patch from the prompt alone, it names too much. Naming
the verification surface is fine (`06` good sample 2 names test files). Naming the
lines to change is not.

Scale the detail to the type. An `mvp` prompt is "deliberately underspecified" by
design (`03` §2.1), and its signal is scope discipline, so pinning every detail
removes the thing being measured. A `feature_implementation` over a public API pins
the interface precisely, because callers depend on it.

## Qualitative requirements

The Studio field is "requirements a unit test cannot settle. These are what make the
task non-trivial". Write them as the senior engineer's version of the task:

- the root cause, not just the fix;
- the existing abstraction that should be reused, by name and path;
- the failure semantics that must hold;
- the scope that must *not* grow.

Every prompt-specific rubric is later derived from the prompt, the environment, or
common engineering knowledge (`03` §5.3), so these requirements are where the rubrics
come from. If one of them can't be turned into a YES/NO question an annotator
could answer from a diff and a trajectory, rewrite it until it can.

Do **not** put them in the prompt. The prompt carries the constraints. The
qualitative requirements carry the judgment the agent is expected to supply on its
own.

## The Harbor package

Copy `templates/harbor-task/` to `tasks/<task-id>/harbor/`, then replace the whole
example. The exporter bug is a demo. Keep its *shapes*:

- **`task.toml` `[metadata]` holds the Studio Task form**: `task_id`,
  `task_format`, `task_type`, `qualitative_requirements`, `repository`,
  `base_commit`, `golden_solution`. Also `stressed_dimensions`, the answer to the
  design question as dimension numbers.
- **The environment is frozen**: base image pinned by digest, repository snapshot
  copied in at the base commit, dependencies baked in, internet disabled. Both
  rollouts must start from an identical state (`03` §3, `04`), so nothing may be
  fetched at trial time.
- **`tests/` is the deterministic gate**, and it tests only what the prompt states.
  The "Deterministic Gate" column of `03` §2.1 is the contract ("repro flips, no
  regressions", "public behavior byte-identical", "failure rate over N runs drops
  below frozen bound"). The qualitative requirements are **not** tested. More than
  one implementation satisfies the prompt, and if a test picks one it becomes
  a hidden requirement. `templates/harbor-task/tests/test_outputs.py` documents this
  split at the top.
- **`solution/solve.sh` is the golden solution**, and it obeys its own prompt. If
  the prompt says to reproduce first, the golden solution reproduces first. Comments
  at the top say what was wrong and why the fix is right. That is the reviewer's
  fastest route to "is this solvable by reasoning".
- **Nothing from `solution/` or `tests/` reaches the agent image.**

For a task over an existing open-source repository, record `repository` and
`base_commit` and copy that exact snapshot into the environment. Verify the
repository's own test suite runs green at that commit inside the image before
writing anything else. A broken baseline is the most expensive defect to find after
rollouts, because every FAIL then has two possible causes (`04`, Annotation Validity).

## Process

Do the work. Don't narrate it, don't present alternatives, and don't produce
design write-ups. The reasoning belongs in `qualitative_requirements` and in the
comment block of `solve.sh`, where the reviewer reads it anyway.

1. **Answer the design question.** Choose internally.
2. **Scaffold** `tasks/<task-id>/harbor/` from `templates/harbor-task/`.
3. **Real content in every file.** No placeholders, no TODOs. The golden solution
   must pass the verifier deterministically.
4. **Prove the gate is a gate.** Run the verifier against:
   - the starting state, which must fail (the task is not already done);
   - the golden solution, which must pass, three times in a row;
   - at least one *different valid* implementation, which must pass. If it fails,
     a test is enforcing an unstated rule;
   - at least one plausible wrong fix per stated constraint, which must fail. If it
     passes, the constraint is unenforced.

   `templates/harbor-task/` was checked exactly this way: original code fails 8/14,
   golden passes 14/14, flush-every-row passes, a raised threshold or a changed
   signature fails.
5. **Run the gate.**

   ```bash
   python3 tasks/gate.py tasks/<task-id>
   ```

   Every BLOCK line must PASS. Each WARN is a decision you make, not something to
   ignore.
6. **Walk the contract audit.** Nothing mechanical catches these.
   - [ ] The prompt names the outcome, the observable behavior, the boundaries and
         the constraints, and nothing that dictates the patch.
   - [ ] Every constraint in the prompt is enforced by a test, or is explicitly a
         qualitative requirement that annotators judge.
   - [ ] Every test traces to a sentence in the prompt.
   - [ ] A valid alternative implementation passes the tests.
   - [ ] The environment contains every convention, helper or exception type a
         qualitative requirement expects the agent to reuse.
   - [ ] Each qualitative requirement converts to a YES/NO rubric answerable from
         a diff and a trajectory.
   - [ ] `stressed_dimensions` names at least two dimensions, and you can point
         at the plausible-wrong path for each one.
   - [ ] The package is bounded: an expert could solve it inside the rollout
         timeout, with no live systems, no production data and no internet.
   - [ ] No unrelated files, caches, notebooks or logs (`04`).
7. **Fill the Studio Task form** from `task.toml` `[metadata]`, and paste the prompt
   from `instruction.md`. Studio's own "Done when" for this step: *the prompt states
   the goal, the constraints, and what must not change, and you can name which of
   the eight dimensions it stresses.*
8. **Freeze.** From here, any change to the prompt, repository, commit, environment,
   tests, harness or limits discards the rollouts (`04`, Frozen Task).

Then hand over to `annotation-prompt.md` for rollouts and scoring.

## Deliverables — exactly these

1. The path to the package: `tasks/<task-id>/harbor/`.
2. The Studio Task form values, in one fenced block in field order, ready to paste:
   Task ID, Task format, Task type, Task prompt (a pointer to `instruction.md`, not a
   copy), Qualitative requirements, Repository, Base commit, Golden solution.
3. The draft prompt-specific rubrics: 5–10 YES/NO questions, each with its mapped
   dimension and source, derived from the prompt, environment and qualitative
   requirements **before any rollout exists** (FIELD-NOTES §1.7).

Then stop. The only thing you may add is a short list of anything broken or
unresolved that needs action before running trajectories. If there's nothing, say
nothing.
