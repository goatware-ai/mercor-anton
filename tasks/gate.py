"""Local pre-submission gate for a Project Anton task.

    python3 tasks/gate.py tasks/<task-id>          # harbor/ package + annotation.json
    python3 tasks/gate.py templates/harbor-task    # a bare Harbor package

BLOCK lines restate a rule the docs make mandatory; the source is cited on each
line. WARN lines are judgment calls with legitimate exceptions — each should be a
decision, not an oversight. This is a local stand-in for Studio's AutoQC
(03-task-workflow.md, "AutoQC Checks"), which cannot be run here.

Where the docs contradict each other, the gate follows the working default in
FIELD-NOTES.md §1 and says so on the line. Extend it whenever a reviewer or
AutoQC sends something back for a reason a script could have caught.

Running it on templates/harbor-task blocks on the REPLACE author fields, which is
correct — it is a template, not a submission.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

TASK_TYPES = {
    "feature_implementation", "bug_fix_deterministic", "bug_fix_nondeterministic",
    "refactor", "architecture_design", "mvp", "codebase_migration",
    "performance_optimization", "test_writing",
}
STATUSES = {"PASS", "PARTIAL", "FAIL"}
ANSWERS = {"YES", "NO"}
# EXPLICIT_PROMPT and COMMON_ENGINEERING_KNOWLEDGE appear in the JSON example; the
# environment source's enum name is not given anywhere (FIELD-NOTES.md §1.8).
SOURCES = {"EXPLICIT_PROMPT", "IMPLICIT_ENVIRONMENT", "COMMON_ENGINEERING_KNOWLEDGE"}
PREFERENCES = {"A_MUCH_BETTER", "A_BETTER", "TIE", "B_BETTER", "B_MUCH_BETTER"}
# Names as Studio's annotation form and 03-task-workflow.md §4 give them. The JSON
# example in the same doc numbers them differently (FIELD-NOTES.md §1.2).
DIMENSIONS = {
    1: "Correctness",
    2: "Architecture, Modularity & Trade-off Soundness",
    3: "Codebase Conventions & Utility Reuse",
    4: "Robustness, Safety & API Stability",
    5: "Instruction Following & Scope Discipline",
    6: "Planning, Research & Tool Proficiency",
    7: "Verification & Testing Discipline",
    8: "Communication: In-flight & Final Summary Quality",
}
CRUFT = re.compile(
    r"(^|/)(__pycache__|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.venv|venv|node_modules"
    r"|\.ipynb_checkpoints|\.idea|\.vscode)(/|$)|(^|/)\.DS_Store$|\.pyc$|\.log$|\.ipynb$|~$"
)
# Undefined qualities that make the bad samples bad (06-samples.md, bad samples 1, 4, 5).
VAGUE = re.compile(
    r"\b(properly|efficient(ly)?|scalable|reliable|modern|instantaneous|heavy load"
    r"|as needed|whatever you think|best (approach|strategy|way)|update anything necessary"
    r"|clean up)\b",
    re.I,
)
NEGATIVE_RUBRIC = re.compile(
    r"\b(did not|didn't|fail(ed)? to|forget|forgot|neglect|duplicate[ds]?|break|broke"
    r"|introduce[ds]? (a )?(bug|regression)|hardcode[ds]?)\b",
    re.I,
)
EVIDENCE = re.compile(r"`|\bstep \d|\bline \d|\.\w{1,5}\b|/\w|\btest_\w|\(\)|::|\bhunk\b", re.I)
FABRICATED = re.compile(r"review|autoqc|iaa|inter.?annotator", re.I)

results = []  # (level, ok, message)


def check(level, ok, message):
    results.append((level, bool(ok), message))


def block(ok, message):
    check("BLOCK", ok, message)


def warn(ok, message):
    check("WARN", ok, message)


def words(text):
    return len(str(text or "").split())


# --------------------------------------------------------------------------- package
def check_package(pkg: Path):
    manifest = pkg / "task.toml"
    block(manifest.is_file(), "task.toml exists (03 §2.2 Harbor format)")
    if not manifest.is_file():
        return {}
    try:
        cfg = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        block(False, f"task.toml parses: {e}")
        return {}
    meta = cfg.get("metadata", {})

    instr = pkg / "instruction.md"
    prompt = instr.read_text(encoding="utf-8") if instr.is_file() else ""
    block(prompt.strip(), "instruction.md exists and is non-empty — it is the task prompt")
    block((pkg / "environment/Dockerfile").is_file(), "environment/Dockerfile exists")
    block((pkg / "solution/solve.sh").is_file(),
          "solution/solve.sh exists (Studio: the golden solution is a tasker output)")

    all_files = [p for p in pkg.rglob("*")]
    text_files = [p for p in all_files if p.is_file() and p.stat().st_size < 2_000_000]
    leftovers = [str(p.relative_to(pkg)) for p in text_files
                 if "REPLACE" in p.read_text(encoding="utf-8", errors="ignore")]
    block(not leftovers, "no REPLACE placeholders left" + (f": {', '.join(leftovers)}" if leftovers else ""))
    cruft = sorted(str(p.relative_to(pkg)) for p in all_files if CRUFT.search(str(p.relative_to(pkg))))
    block(not cruft, "no caches, env folders, notebooks or logs in the package (04, Required Artifacts)"
          + (f": {', '.join(cruft[:6])}" if cruft else ""))

    for key in ("task_id", "task_format", "task_type", "qualitative_requirements", "golden_solution"):
        block(str(meta.get(key, "")).strip(), f"[metadata].{key} is set (Studio Task form, required field)")
    block(meta.get("task_type") in TASK_TYPES,
          f"[metadata].task_type is one of the nine task types (03 §2.1) — got {meta.get('task_type')!r}")
    warn(meta.get("task_format") == "Terminal Bench",
         "[metadata].task_format is \"Terminal Bench\" (walkthrough §1; FIELD-NOTES §1.5)")
    warn(words(meta.get("qualitative_requirements")) >= 20,
         "qualitative_requirements is specific enough to derive rubrics from (≥20 words)")
    stressed = meta.get("stressed_dimensions") or []
    warn(len(stressed) >= 2 and all(isinstance(d, int) and 1 <= d <= 8 for d in stressed),
         "[metadata].stressed_dimensions names ≥2 of dimensions 1-8 (walkthrough: 'Done when')")
    warn(bool(meta.get("repository")) == bool(meta.get("base_commit")),
         "repository and base_commit are set together (both rollouts start from one commit)")

    env = cfg.get("environment", {})
    warn(env.get("allow_internet") is False, "[environment].allow_internet = false (03 §3)")

    dockerfiles = [p for p in (pkg / "environment").glob("Dockerfile*") if p.is_file()]
    unpinned = []
    for df in dockerfiles:
        for line in df.read_text(encoding="utf-8").splitlines():
            if re.match(r"\s*FROM\s", line, re.I) and "@sha256:" not in line:
                unpinned.append(f"{df.name}: {line.strip()}")
    warn(not unpinned, "every FROM is digest-pinned, so the environment stays frozen (04)"
         + (f": {'; '.join(unpinned)}" if unpinned else ""))
    solution_in_env = [df.name for df in dockerfiles
                       if re.search(r"^\s*(COPY|ADD)\s.*\b(solution|tests)/", df.read_text(encoding="utf-8"), re.M)]
    block(not solution_in_env, "environment image copies nothing from solution/ or tests/")

    test_sh = pkg / "tests/test.sh"
    if (pkg / "tests").is_dir():
        body = test_sh.read_text(encoding="utf-8") if test_sh.is_file() else ""
        block(body, "tests/test.sh exists when tests/ does")
        block("/logs/verifier/reward" in body, "tests/test.sh writes /logs/verifier/reward.txt")
        warn(not re.search(r"^\s*set\s+-\w*e", body, re.M),
             "tests/test.sh has no `set -e` — a failing test must still reach the reward write")
        banned = re.findall(r"\b(pip3? install|uv (pip|add|sync)|uvx|npm (i|install)|curl|wget|git clone"
                            r"|apt(-get)? install)\b", body)
        block(not banned, "tests/test.sh installs nothing at trial time — rollouts have no internet")
    else:
        warn(False, "tests/ is present (optional per 03 §2.2, but it is the deterministic gate)")

    if prompt:
        vague = sorted({m.group(0).lower() for m in VAGUE.finditer(prompt)})
        warn(not vague, "prompt avoids undefined qualities (06 bad samples)"
             + (f": {', '.join(vague)}" if vague else ""))
        warn(words(prompt) >= 25, "prompt is long enough to define observable behavior (06: vague/trivial)")
        warn(not re.search(r"\b(open|edit|change)\s+\S+\.(py|js|ts|go|rs|java|php|rb|c|h)\b.*\b(remov|replac|add)", prompt, re.I),
             "prompt does not dictate the patch (06 bad sample 2: solution-leaking)")
        warn(re.search(r"\b(do not|don't|must not|never|without)\b", prompt, re.I),
             "prompt states at least one explicit constraint (Studio: files not modified, interfaces, scope)")
    return meta


# ------------------------------------------------------------------------ annotation
def check_annotation(path: Path, meta: dict, task_dir: Path):
    try:
        ann = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        block(False, f"annotation.json is valid JSON: {e}")
        return
    block(isinstance(ann, dict), "annotation.json is a JSON object")
    if not isinstance(ann, dict):
        return

    required = ["task_id", "task_type", "trajectory_a_path", "trajectory_b_path",
                "part_0_goal_completeness", "prompt_specific_rubrics", "global_dimensions",
                "final_quality_score_a", "final_quality_score_b", "pairwise_evaluation"]
    missing = [k for k in required if k not in ann]
    block(not missing, "annotation has every required key (03 §6)" + (f": missing {', '.join(missing)}" if missing else ""))
    invented = [k for k in ann if FABRICATED.search(k)]
    block(not invented, "no reviewer / AutoQC / IAA values in the annotation (03: do NOT fabricate)"
          + (f": {', '.join(invented)}" if invented else ""))
    block(ann.get("task_type") in TASK_TYPES, f"task_type is a valid enum — got {ann.get('task_type')!r}")
    if meta:
        block(ann.get("task_id") == meta.get("task_id"), "annotation task_id matches task.toml")
        block(ann.get("task_type") == meta.get("task_type"), "annotation task_type matches task.toml")
    for side in ("a", "b"):
        ref = str(ann.get(f"trajectory_{side}_path", ""))
        block(ref.strip() and "<" not in ref, f"trajectory_{side}_path is filled in")
        local = task_dir / ref
        warn(not ref or local.is_file() or not ref.endswith(".json"),
             f"trajectory_{side}_path resolves to a file in the task folder ({ref})")
    block(ann.get("trajectory_a_path") != ann.get("trajectory_b_path"), "A and B are different trajectories")

    # Dimension 0
    gc = ann.get("part_0_goal_completeness") or {}
    sa, sb = gc.get("status_a"), gc.get("status_b")
    block(sa in STATUSES and sb in STATUSES, f"Dimension 0 statuses are PASS/PARTIAL/FAIL — got {sa!r}, {sb!r}")
    block(not (sa == "FAIL" and sb == "FAIL"), "not both trajectories FAIL — regenerate the pair (03 §3)")
    warn("FAIL" not in (sa, sb),
         "both trajectories PASS or PARTIAL — a single FAIL is allowed only if it is the Gemini one, "
         "and AutoQC/the reviewer checklist still flag it (FIELD-NOTES §1.1)")
    block(words(gc.get("reason")) >= 8, "Dimension 0 has a written reason")

    # Prompt-specific rubrics
    rubrics = ann.get("prompt_specific_rubrics") or []
    block(5 <= len(rubrics) <= 10, f"5-10 prompt-specific rubrics (03 §5) — got {len(rubrics)}")
    ids = [r.get("rubric_id") for r in rubrics if isinstance(r, dict)]
    block(len(ids) == len(set(ids)) == len(rubrics), "rubric_id values are present and unique")
    per_dim = {}
    for i, r in enumerate(rubrics, 1):
        if not isinstance(r, dict):
            block(False, f"rubric {i} is an object")
            continue
        tag = r.get("rubric_id") or f"#{i}"
        dim = r.get("mapped_dimension")
        block(isinstance(dim, int) and not isinstance(dim, bool) and 1 <= dim <= 8,
              f"{tag}: mapped_dimension is an integer 1-8 (03 §5.1)")
        per_dim[dim] = per_dim.get(dim, 0) + 1
        block(r.get("source") in SOURCES, f"{tag}: source is one of the three legitimate sources (03 §5.3)")
        block(r.get("answer_a") in ANSWERS and r.get("answer_b") in ANSWERS, f"{tag}: answer_a/answer_b are YES or NO")
        stmt = str(r.get("statement", ""))
        block(words(stmt) >= 6, f"{tag}: statement is written out")
        warn(not NEGATIVE_RUBRIC.search(stmt), f"{tag}: framed so YES is the good answer (03 §5.2)")
        block(words(r.get("reason")) >= 8, f"{tag}: has a written reason")
        warn(EVIDENCE.search(str(r.get("reason", ""))), f"{tag}: reason cites evidence — a step, file, test or hunk")
    warn(len({d for d in per_dim if d}) >= 2, "rubrics span more than one dimension")

    # Global dimensions
    dims = ann.get("global_dimensions") or []
    got = sorted(d.get("dimension_id") for d in dims if isinstance(d, dict) and isinstance(d.get("dimension_id"), int))
    block(got == list(range(1, 9)) and len(dims) == 8, f"exactly eight global dimensions, ids 1-8 once each — got {got}")
    scores = {"a": [], "b": []}
    for d in dims:
        if not isinstance(d, dict):
            continue
        did = d.get("dimension_id")
        for side in ("a", "b"):
            s = d.get(f"score_{side}")
            ok = isinstance(s, int) and not isinstance(s, bool) and 1 <= s <= 5
            block(ok, f"dimension {did}: score_{side} is an integer 1-5")
            if ok:
                scores[side].append(s)
        warn(d.get("name") == DIMENSIONS.get(did),
             f"dimension {did}: name matches Studio ({DIMENSIONS.get(did)!r}) — got {d.get('name')!r}")
        reason = str(d.get("reason", ""))
        block(words(reason) >= 12, f"dimension {did}: reason is more than a restated score (walkthrough)")
        warn(EVIDENCE.search(reason), f"dimension {did}: reason cites the step or the code")

    # Final score and preference
    final = {}
    for side in ("a", "b"):
        value = ann.get(f"final_quality_score_{side}")
        block(isinstance(value, (int, float)) and not isinstance(value, bool),
              f"final_quality_score_{side} is a number")
        final[side] = value if isinstance(value, (int, float)) else None
        if len(scores[side]) == 8 and final[side] is not None:
            mean = round(sum(scores[side]) / 8, 2)
            block(abs(final[side] - mean) < 0.005,
                  f"final_quality_score_{side} = mean of dimensions 1-8 to two decimals ({mean}) (FIELD-NOTES §1.4)")
    pe = ann.get("pairwise_evaluation") or {}
    pref = pe.get("preference")
    block(pref in PREFERENCES, f"preference is a valid enum — got {pref!r}")
    block(words(pe.get("comparative_rationale")) >= 20, "comparative_rationale is written out")
    if None not in final.values() and pref in PREFERENCES:
        if final["a"] > final["b"]:
            block(pref.startswith("A_"), "preference direction agrees with final scores (7.1: higher score = preferred)")
        elif final["b"] > final["a"]:
            block(pref.startswith("B_"), "preference direction agrees with final scores (7.1: higher score = preferred)")
        else:
            warn(pref == "TIE", "equal final scores come with TIE, or the rationale explains the tiebreak")
        gap = abs(final["a"] - final["b"])
        warn(not (pref.endswith("MUCH_BETTER") and gap < 0.5),
             f"*_MUCH_BETTER is backed by a real score gap (got {gap:.2f})")
        warn(not (pref == "TIE" and gap >= 1),
             f"TIE is not paired with a ≥1 point score gap (got {gap:.2f})")


# ------------------------------------------------------------------------------ main
def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = Path(sys.argv[1]).resolve()
    pkg = root / "harbor" if (root / "harbor/task.toml").is_file() else root
    meta = check_package(pkg)
    annotation = root / "annotation.json"
    if annotation.is_file():
        check_annotation(annotation, meta, root)
    elif pkg != root:
        warn(False, "annotation.json present (skipped annotation checks)")

    blocked = 0
    for level, ok, message in results:
        status = "PASS" if ok else level
        blocked += level == "BLOCK" and not ok
        print(f"{status:5}  {message}")
    warns = sum(1 for level, ok, _ in results if level == "WARN" and not ok)
    print(f"\n{blocked} blocking, {warns} warnings — {'DO NOT SUBMIT' if blocked else 'ok to submit'}")
    print("Not checkable here: which trajectory is Gemini, that A/B share harness/prompt/commit, "
          "whether rubrics were written before reading the diffs, and whether each reason is true.")
    sys.exit(1 if blocked else 0)


if __name__ == "__main__":
    main()
